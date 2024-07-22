import json
import threading
import queue
import time
import atexit

from websocket_server import WebsocketServer
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging
from logging.handlers import QueueHandler, QueueListener
from farmbot_api.lettuce_farmbot import LettuceFarmbot
from farmbot_api.json_tools import read_json
import sys
from concurrent.futures import ThreadPoolExecutor
from farmbot_api import lettuce_farmbot

# Setting up logging configuration
log_queue = queue.Queue()

stream_handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

queue_handler = QueueHandler(log_queue)
logger = logging.getLogger(__name__)
logger.addHandler(queue_handler)
logger.setLevel(logging.DEBUG)

listener = QueueListener(log_queue, stream_handler)
listener.start()

# Ensure logging configuration is set up first
logger.info("Logging setup complete")

# Infos for farmbot (will later be received from frontend)
logger.debug("Reading login information for farmbot")
farmbot_name = "farmbot"
login = read_json("logins.json")[farmbot_name]

# there was farmbot initialization here

logger.debug("Connecting to MongoDB")
client = MongoClient("mongodb://mongo:27017/")
db = client.mydatabase
users_collection = db.users
jobs_collection = db.jobs
plant_collection = db.plants

# Ensure a default user exists
logger.debug("Checking for default user")
if not users_collection.find_one({"name": "user", "password": "lettuce"}):
    inserted_id_user = users_collection.insert_one({"name": "user", "password": "lettuce"}).inserted_id
    logger.info(f"Inserted default user with ID: {inserted_id_user}")

# Initialize job queue and worker thread
job_queue = queue.Queue()
stop_worker = threading.Event()


def worker_thread():
    while not stop_worker.is_set():
        job = job_queue.get()
        if job is None:
            break  # Exit the loop if a None job is received (for shutdown purposes)
        try:
            job_positions, JobType, job_id = job  # Unpack the job tuple correctly
            if JobType == "Watering":
                current_time = time.time()
                # Update the job with the last execution time
                jobs_collection.update_one({"_id": job_id}, {"$set": {"lastExecutionTime": current_time}})
            logger.debug(f"Processing job: {job}")
            handle_farmbot_api(job_positions, JobType, job_id)
        except Exception as e:
            logger.error(f"Error processing job: {e}")
        finally:
            job_queue.task_done()


# Start the worker thread
worker = threading.Thread(target=worker_thread, daemon=True)
worker.start()


def handle_execute_job(client, server, data):
    # logger.debug("handle_execute_job called")
    job_id = data.get('_id')
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    # logger.debug(f"Job fetched: {job}")
    job_positions = []
    JobType = job.get("jobType")
    if JobType == "Seeding":
        job_data = {"seedType": job["seedType"], "seedingDepth": job["seedingDepth"],
                    "plantDistance": job["plantDistance"], "x0": job["x0"], "y0": job["y0"], "x1": job["x1"],
                    "y1": job["y1"]}
        plant_positions = calculate_plant_positions(job_data)
        for p in plant_positions:
            plant_id = plant_collection.insert_one(
                {"x": p["x"], "y": p["y"], "seedType": job["seedType"], "seedingDepth": job["seedingDepth"],
                 "plantedBy": job_id, "plantDistance": job["plantDistance"]}).inserted_id
            # logger.info(f"Inserted plant positions with ID: {plant_id}")
        job_positions = plant_positions
        job_queue.put((job_positions, JobType, job_id))

    elif JobType == "Watering":
        # iterate over all plants of same type in DB
        plantCursor = plant_collection.find({"seedType": job["seedType"]})
        for plant in plantCursor:
            nozzleHeight = -495 + job["height"]
            job_positions.append(
                {"x": plant["x"], "y": plant["y"], "volume": job["WateringAmount"], "watering_height": nozzleHeight})
        # logger.debug(f"farmbot_data: {job_positions}")
        # logger.info(job_positions)
        # logger.info(JobType)
        job_queue.put((job_positions, JobType, job_id))


def calculate_plant_positions(job):
    # logger.debug("calculate_plant_positions called")
    plant_distance = job["plantDistance"]
    x0, y0 = job["x0"], job["y0"]
    x1, y1 = job["x1"], job["y1"]
    border_distance = int(plant_distance / 2)

    # coordinates have to "go up" in order do shrink the working area to respect the plant distance on the borders
    adjusted_x0 = x0 + border_distance
    adjusted_y0 = y0 + border_distance

    # coordinates have to "go down" in order to shrink the working area to respect the plant distance on the borders
    adjusted_x1 = x1 - border_distance
    adjusted_y1 = y1 - border_distance

    # Calculate the individual positions
    plant_positions = []
    # needs the +1 to *not* cut the last valid location
    x_positions = list(range(adjusted_x0, adjusted_x1 + 1, plant_distance))
    y_positions = list(range(adjusted_y0, adjusted_y1 + 1, plant_distance))
    for x in x_positions:
        for y in y_positions:
            plant_positions.append({"x": x, "y": y})
    # logger.debug(f"Plant positions calculated: {plant_positions}")
    return plant_positions
    # the range function and the properly shrunken border assure that there is no plant outside the safe area
    # (which is the original working area - plantDistance/2 so that every plant has enough space to the border of the
    # working area)


def handle_farmbot_api(data, JobType, job_id):
    # logger.debug(f"Raw Data: {data}")
    # Create a farmbot instance and connect
    # Make sure to enter a tool_name if a tool is connected!!!
    logger.debug("Creating LettuceFarmbot instance")
    farmbot = LettuceFarmbot(farmbot_name, login)
    try:
        logger.debug("Connecting to Farmbot")
        farmbot.connect()
        logger.debug("Farmbot Connected")
        if JobType == "Seeding":
            logger.debug("Job execution Dispatched")
            jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": {"job_status": "active"}})
            farmbot.execute_seeding_job(data)
        elif JobType == "Watering":
            logger.debug("Job execution Dispatched")
            jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": {"job_status": "active"}})
            farmbot.execute_watering_jobs(data)
    except Exception as e:
        logger.error(f"Error during job execution: {e}")
    finally:
        jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": {"job_status": "inactive"}})
        farmbot.disconnect()
        logger.debug("Farmbot Disconnected")


def handle_register(client, server, data):
    # logger.debug("handle_register called")
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        server.send_message(client, json.dumps({"error": "Name and password are required"}))
        return

    existing_user = users_collection.find_one({"name": name})
    if existing_user:
        server.send_message(client, json.dumps({"error": "User already exists"}))
        return

    user_id = users_collection.insert_one({"name": name, "password": password}).inserted_id
    new_user = users_collection.find_one({"_id": ObjectId(user_id)})

    server.send_message(client, json.dumps({"message": "User registered successfully", "_id": str(new_user["_id"])}))
    # logger.info(f"User {name} registered with ID: {user_id}")


def handle_authenticate(client, server, data):
    # logger.debug("handle_authenticate called")
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({"name": username, "password": password})

    if user:
        server.send_message(client,
                            json.dumps({"authenticated": True, "user_id": str(user["_id"]), "name": str(user["name"])}))
        # logger.info(f"User {username} authenticated successfully")
    else:
        server.send_message(client, json.dumps({"authenticated": False}))
        # logger.warning(f"Failed authentication attempt for user {username}")


def handle_submit_job(client, server, data):
    # logger.debug("handle_submit_job called")
    job_id = jobs_collection.insert_one(data).inserted_id
    new_job = jobs_collection.find_one({"_id": ObjectId(job_id)})

    server.send_message(client, json.dumps(
        {"message": "Job data received and inserted into database", "_id": str(new_job["_id"])}))
    # logger.info(f"Job submitted with ID: {job_id}")


def handle_get_jobs(client, server):
    # logger.debug("handle_get_jobs called")
    jobs = jobs_collection.find()
    results = []

    for job in jobs:
        JobType = job.get("jobType")
        if JobType == "Seeding":
            results.append({"_id": str(job["_id"]), "user_id": job["user_id"], "name": job["name"],
                            "job_status": job["job_status"], "jobType": job["jobType"], "seedType": job["seedType"],
                            "seedingDate": job["seedingDate"], "seedingDepth": job["seedingDepth"],
                            "plantDistance": job["plantDistance"], "x0": job["x0"], "y0": job["y0"], "x1": job["x1"],
                            "y1": job["y1"]})
        elif JobType == "Watering":
            # logger.debug(f"Fetching plants for seedType: {job['seedType']}")
            plant_amount = plant_collection.count_documents({"seedType": job["seedType"]})
            # logger.debug(f"Found {plant_amount} plants for seedType: {job['seedType']}")
            total_water_consumption = plant_amount * job["WateringAmount"]
            # logger.debug(f"Total water consumption for job {job['_id']}: {total_water_consumption}")
            results.append({"_id": str(job["_id"]), "user_id": job["user_id"], "name": job["name"],
                            "job_status": job["job_status"], "jobType": job["jobType"], "seedType": job["seedType"],
                            "wateringDate": job["wateringDate"], "Interval": job["Interval"],
                            "WateringAmount": job["WateringAmount"], "height": job["height"],
                            "total_water_consumption": total_water_consumption})
        else:
            logger.warning("Unknown Job Type")

    server.send_message(client, json.dumps(results))
    logger.info("Jobs retrieved and sent to client")


def handle_update_job(client, server, data):
    # logger.debug("handle_update_job called")
    job_id = data.get('_id')
    if not job_id:
        server.send_message(client, json.dumps({"error": "Job ID is required"}))
        return

    update_data = {key: value for key, value in data.items() if key != '_id' and key != 'action'}
    # logger.debug(f"Update data: {update_data}")

    results = jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": update_data})
    if results.matched_count:
        server.send_message(client, json.dumps({"message": "Job updated successfully"}))
        # logger.info(f"Job {job_id} updated successfully")
    else:
        server.send_message(client, json.dumps({"message": "No job found with provided ID"}))
        # logger.warning(f"No job found with ID: {job_id}")


def handle_delete_job(client, server, data):
    # logger.debug("handle_delete_job called")
    job_id = data.get('_id')
    if not job_id:
        server.send_message(client, json.dumps({"error": "Job ID is required"}))
        return

    results = jobs_collection.delete_one({"_id": ObjectId(job_id)})
    if results.deleted_count:
        server.send_message(client, json.dumps({"message": "Job deleted successfully"}))
        # logger.info(f"Job {job_id} deleted successfully")
    else:
        server.send_message(client, json.dumps({"message": "No job found with provided ID"}))
        # logger.warning(f"No job found with ID: {job_id}")


def handle_status(client, server):
    # logger.debug("handle_status called")
    # logger.debug("Creating LettuceFarmbot instance")
    farmbot = LettuceFarmbot(farmbot_name, login)

    def send_status():
        try:
            # logger.debug("Connecting to Farmbot")
            farmbot.connect()
            # logger.debug("Farmbot Connected")
            while True:
                # Check if the client is still connected
                if client not in server.clients:
                    logger.debug("Client disconnected, stopping status updates")
                    break

                # Send farmbot status to client
                server.send_message(client, json.dumps({"status": farmbot.status}))
                # logger.debug(f"Sent status: {farmbot.status}")

                # Exit loop if farmbot is offline
                #                 if farmbot.status == "offline":
                #                     break

                time.sleep(1)  # Check every second
        except Exception as e:
            logger.error(f"Error during status check: {e}")
        finally:
            farmbot.disconnect()
            logger.debug("Farmbot Disconnected")

    # Start the status sending in a new thread
    status_thread = threading.Thread(target=send_status)
    status_thread.start()

def handle_send_area(client, server, data):
    logger.debug("handle_send_area called")
    area = data.get("area")
    plant_pos_temp = calculate_plant_positions(area)
    #logger.debug(f"Area is {area}")
    #logger.debug(f"Temp Plant pos is {plant_pos_temp}")
    adjustment_factor = 2700 / 870
    adjusted_plant_pos = [{"x": pos["x"] / adjustment_factor, "y": pos["y"] / adjustment_factor} for pos in plant_pos_temp]
    server.send_message(client, json.dumps({"action": "calculated-plant-positions", "data": adjusted_plant_pos}))


def handle_get_planted_seeds(client, server):
    # logger.debug("handle_get_planted_seeds called")
    seeds = plant_collection.find({})
    planted_seeds_data = [{"x": seed["x"] / (2700 / 870), "y": seed["y"] / (2700 / 870), "seedType": seed["seedType"],
                           "plantDistance": seed["plantDistance"]} for seed in seeds]
    # logger.debug(f"Seed List is:{planted_seeds_data}")
    server.send_message(client, json.dumps({"action": "planted-seeds-data", "data": planted_seeds_data}))


stop_scheduler = threading.Event()


def schedule_watering_jobs():
    while not stop_scheduler.is_set():
        # Retrieve all watering jobs that need to be executed based on their interval
        current_time = time.time()
        # logger.info(current_time)
        watering_jobs = jobs_collection.find({"jobType": "Watering"})
        for job in watering_jobs:
            interval_seconds = job["Interval"] * 3600  # Convert hours to seconds
            # "0" is the default value when "lastExecutionTime" doesn't exist in the doc
            last_execution_time = job.get("lastExecutionTime", job["JobDate"]+interval_seconds)
            # logger.info(last_execution_time)
            # logger.info(f"current time {current_time}")
            # logger.info(f"last_execution time {last_execution_time}")
            # logger.info(f"interval_seconds {interval_seconds}")
            if current_time - last_execution_time >= interval_seconds:
                # send job ID to the handle execute function and it will do the rest automatically
                # logger.info(f"sending data{job["_id"]}")
                handle_execute_job(None, None, {"_id": job["_id"]})

        # logger.info('Check complete, sleeping 60s')
        time.sleep(60)  # Check every minute


# Start the scheduling thread
scheduler_thread = threading.Thread(target=schedule_watering_jobs, daemon=True)
scheduler_thread.start()


def message_received(client, server, message):
    # logger.debug("message_received called")
    try:
        data = json.loads(message)
        action = data.get('action')
        if action == 'register':
            handle_register(client, server, data)
        elif action == 'authenticate':
            handle_authenticate(client, server, data)
        elif action == 'submit-job':
            handle_submit_job(client, server, data)
        elif action == 'get-jobs':
            handle_get_jobs(client, server)
        elif action == 'update-job':
            handle_update_job(client, server, data)
        elif action == 'delete-job':
            handle_delete_job(client, server, data)
        elif action == 'execute-job':
            handle_execute_job(client, server, data)
        elif action == 'get-status':
            handle_status(client, server)
        elif action == 'get-planted-seeds':  # New action for getting planted seeds
            handle_get_planted_seeds(client, server)
        elif action == 'send-area':
            handle_send_area(client, server, data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
         logger.error(f"Error handling message: {e}")

server = WebsocketServer(host='0.0.0.0', port=5000)
server.set_fn_message_received(message_received)

logger.info('Starting server...')
server.run_forever()


def shutdown():
    stop_worker.set()  # Signal the worker thread to stop
    job_queue.put(None)  # Enqueue a None to unblock the worker thread if it's waiting
    worker.join()  # Wait for the worker thread to terminate
    logger.info("Worker thread terminated gracefully")
    stop_scheduler.set()  # Signal the scheduler thread to stop
    logger.info("Scheduler thread terminated gracefully")


atexit.register(shutdown)
