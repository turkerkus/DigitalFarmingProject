import React, { useState, useEffect, useRef, useContext } from 'react';
import '../styles/Dashboard.css';
import FieldSelector from './FieldSelector';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { Formik, Field, Form, ErrorMessage } from 'formik';
import { seedingJobSchema, wateringJobSchema } from './validationSchema';
import { AuthContext } from '../contexts/AuthContext';
import Header from './Header';
import StatusDisplay from './StatusDisplay';
import WebSocketComponent from "./WebSocketComponent";
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user_id, name } = useContext(AuthContext);
  const [workingArea, setWorkingArea] = useState({ x0: 0, y0: 0, x1: 100, y1: 100 });
  const [eventCount, setEventCount] = useState(0);
  const [darkmode, setDarkmode] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [seedingDate, setSeedingDate] = useState(new Date());
  const formikRef = useRef(null);
  const [wateringDate, setWateringDate] = useState(new Date());
  const [showWForm, setShowWForm] = useState(false);
  const [JobData, setJobData] = useState([]);
  const [showSeedingTasks, setShowSeedingTasks] = useState(false);
  const [showWateringTasks, setShowWateringTasks] = useState(false);
  const [showSensors, setShowSensors] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [active,setActive] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      sessionStorage.setItem('isRefreshed', 'true');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  useEffect(() => {
    if (sessionStorage.getItem('isRefreshed')) {
      sessionStorage.removeItem('isRefreshed');
      navigate('/');
    }}, []);

  const handleLogout = () => {
    navigate('/');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };
  const convertToUnix = (date) => {
    return Math.floor(new Date(date).getTime() / 1000);
  };


  const fetchJobData = async () => {
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      socket.send(JSON.stringify({ action: 'get-jobs' }));
    };

    socket.onmessage = (event) => {
      let data = JSON.parse(event.data);
      if (!Array.isArray(data)) {
        console.log(data);
        throw new TypeError('Expected an array but got ' + typeof data);
      }

      const datafiltered = data.filter((x) => x.user_id === user_id);
      setJobData(datafiltered);

      const active = datafiltered.find(job => job.job_status === "active");
      setActive(active);
      console.log('Job Data from DB: ', JSON.stringify(datafiltered, null, 2));
      console.log('Updated JobData state:', datafiltered);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  useEffect(() => {
    const intervalId = setInterval(async () => {
      await fetchJobData();
    }, 2000);

    // Clean up the interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const isOverlapping = (newJob, existingJobs) => {
    const newJobStart = new Date(newJob.seedingDate || newJob.wateringDate).getTime();
    const newJobEnd = newJobStart + (newJob.Interval || 0) * 60000; // Assume that each task requires a certain time interval in minutes
    return existingJobs.some(job => {
      const jobStart = new Date(job.seedingDate || job.wateringDate).getTime();
      const jobEnd = jobStart + (job.Interval || 0) * 60000;
      return (newJobStart < jobEnd && jobStart < newJobEnd);
    });
  };

  const handleSubmitJob = async (values, { setSubmitting }) => {
    console.log('Job Data:', values, workingArea);

    let constrainedValues = { ...values };

    if (values.jobType === 'Seeding') {
      constrainedValues = {
        ...values,
        x0: Math.ceil(values.x0 * (2700 / 870)),
        x1: Math.ceil(Math.min(values.x1, 870) * (2700 / 870)),
        y0: Math.ceil(values.y0 * (2700 / 870)),
        y1: Math.ceil(Math.min(values.y1, 435) * (2700 / 870)),
        JobDate: convertToUnix(values.seedingDate),
      };
    }
    else if (values.jobType === 'Watering') {
      constrainedValues = { ...values,
        JobDate: convertToUnix(values.wateringDate),
        height: values.height * 10,};
    }
    console.log('Job Data:', constrainedValues, workingArea);


    // Check that new tasks do not overlap with the time of existing tasks
    if (isOverlapping(constrainedValues, JobData)) {
      alert('Mission times conflict, please choose a different time');
      setSubmitting(false);
      return;
    }

    try {
      const socket = new WebSocket('ws://localhost:5000');
      const payload = {
        action: 'submit-job',
        user_id: user_id,
        name: name,
        ...constrainedValues,
        job_status: "inactive",
      };
      if (currentJob && currentJob._id) {
        payload.action = 'update-job';
        payload._id = currentJob._id;
      }

      socket.onopen = () => {
        console.log('Sending payload:', payload);
        socket.send(JSON.stringify(payload));
      };

      socket.onmessage = (event) => {
        const result = JSON.parse(event.data);
        console.log('Submit response:', result);
        fetchJobData();
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error submitting job data:', error);
    }
    setSubmitting(false);
    setShowForm(false);
    setShowWForm(false);
    setCurrentJob(null);
    setShowTable(true);
  };

  const handleDeleteJob = async (id) => {
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      const payload = { action: 'delete-job', _id: id };
      socket.send(JSON.stringify(payload));
    };

    socket.onmessage = (event) => {
      const result = JSON.parse(event.data);
      console.log('Delete Job Response:', result);
      fetchJobData();
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const handleEditJob = (job) => {
    if (currentJob && currentJob._id === job._id) {
      setShowForm(false);
      setShowWForm(false);
      setCurrentJob(null);
    } else {
      setCurrentJob(job);
      if (job.jobType === 'Seeding') {
        setShowForm(true);
        setShowWForm(false);
      } else if (job.jobType === 'Watering') {
        setShowWForm(true);
        setShowForm(false);
      }
    }
  };

  const handleExecuteJob = (id) => {
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      const payload = { action: 'execute-job', _id: id };
      socket.send(JSON.stringify(payload));
    };

    socket.onmessage = (event) => {
      console.log('Message from server ', event.data);
    };

    socket.onerror = (error) => {
      console.log('WebSocket Error: ', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket closed: ', event);
    };
  };

  const handleToggle = (type) => {
    if (type === "seed") {
      setShowForm(!showForm);
      setShowWForm(false);
      setCurrentJob(null);
    } else if (type === "water") {
      setShowWForm(!showWForm);
      setShowForm(false);
      setCurrentJob(null);
    }
  };

  const toggleTaskList = (taskType) => {
    if(showSidebar){
      setShowSeedingTasks(taskType === 'seeding');
      setShowWateringTasks(taskType === 'watering');}
    else{
      setShowSeedingTasks(taskType === 'seeding');
      setShowWateringTasks(taskType === 'watering');
      toggleSidebar();
    }
  };

  const toggleSidebar = () => {
    setShowSidebar(!showSidebar);
  };

  useEffect(() => {
    fetchJobData();
  }, []);

  useEffect(() => {
    if ((showForm || showWForm) && formikRef.current) {
      formikRef.current.setFieldValue('x0', Math.ceil(workingArea.x0));
      formikRef.current.setFieldValue('y0', Math.ceil(workingArea.y0));
      formikRef.current.setFieldValue('x1', Math.ceil(workingArea.x1));
      formikRef.current.setFieldValue('y1', Math.ceil(workingArea.y1));
    }
  }, [workingArea, showForm, showWForm]);

  return (
      <>
        <div className={darkmode ? "header-container headerdark" : "header-container"}>
          <Header/>
          <button className="logout-button" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i> Logout
          </button>
        </div>
        <div className="dashboard-container">
          <div className={darkmode ? "navbardark" : "navbar"}>
            <div className="nav-item" onClick={toggleSidebar}>
              <i className="fas fa-bars"></i>
            </div>
            <div className="nav-item" onClick={() => toggleTaskList('seeding')}>
              <i className="fa-solid fa-seedling"></i> Seeding Task
            </div>
            <div className="nav-item" onClick={() => toggleTaskList('watering')}>
              <i className="fa-solid fa-hand-holding-droplet"></i> Watering Task
            </div>
            <div className="nav-item" onClick={() => setDarkmode(!darkmode)}>
              {darkmode ? <i className="fa-solid fa-moon"></i> : (<i className="fa-regular fa-moon"></i>)}
            </div>
          </div>

          <div className="content-wrapper">
            {showSidebar && (
                <div className={darkmode ? "sidebardark" : "sidebar"}>
                  {showSeedingTasks && (
                      <div className="task-list">
                        <button onClick={() => handleToggle("seed")}>
                          <i className="fas fa-plus"></i> Create Seeding
                        </button>
                        <button onClick={() => setShowTable(!showTable)}>
                          <i className="fas fa-eye"></i> Show {showTable ? '▲' : '▼'}
                        </button>
                      </div>
                  )}
                  {showWateringTasks && (
                      <div className="task-list">
                        <button onClick={() => handleToggle("water")}>
                          <i className="fas fa-plus"></i> Create Watering
                        </button>
                        <button onClick={() => setShowTable(!showTable)}>
                          <i className="fas fa-eye"></i> Show {showTable ? '▲' : '▼'}
                        </button>
                      </div>
                  )}
                  {showTable && !showSensors && (
                      <div className="job-list">
                        {JobData.map((job) => (
                            (active?job._id !== active._id:true) && (
                                <div key={job._id} className={darkmode ? "job-itemdark" : "job-item"}>
                                  <h3>{job.jobType === 'Seeding' ? 'Seeding Type' : 'Watering Type'}: {job.seedType}</h3>
                                  <p>{job.jobType === 'Seeding' ? 'Seeding' : 'Watering'} Date: {formatDate(job.seedingDate || job.wateringDate)}</p>
                                  {job.jobType === 'Seeding' ? (
                                      <>
                                        <p>Depth: {job.seedingDepth} mm</p>
                                        <p>Distance: {job.plantDistance} mm</p>
                                        <p className="inactive">Job status: {job.job_status}</p>
                                      </>
                                  ) : (
                                      <>
                                        <p>Interval: {job.Interval} h</p>
                                        <p>Watering Amount: {job.WateringAmount} ml</p>
                                        <p>Watering Nozzle Height: {job.height / 10} cm</p>
                                        <p>Total Water Consumption: {job.total_water_consumption} ml</p>
                                        <p className="inactive">Job status: {job.job_status}</p>
                                      </>
                                  )}
                                  <div className="button-group">
                                    <button className="execute-button" onClick={() => handleExecuteJob(job._id)}>Execute
                                    </button>
                                    <button className="modify-button" onClick={() => handleEditJob(job)}>Modify</button>
                                    <button className="delete-button" onClick={() => handleDeleteJob(job._id)}>Delete
                                    </button>
                                  </div>
                                </div>
                            )))}

                        {active&&(
                            <div key={active._id} className={darkmode ? "job-itemdark" : "job-item"}>
                              <h3>{active.jobType === 'Seeding' ? 'Seeding Type' : 'Watering Type'}: {active.seedType}</h3>
                              <p>{active.jobType === 'Seeding' ? 'Seeding' : 'Watering'} Date: {formatDate(active.seedingDate || active.wateringDate)}</p>
                              {active.jobType === 'Seeding' ? (
                                  <>
                                    <p>Depth: {active.seedingDepth} mm</p>
                                    <p>Distance: {active.plantDistance} mm</p>
                                    <p className="active">Job status: {active.job_status}</p>
                                  </>
                              ) : (
                                  <>
                                    <p>Interval: {active.Interval} h</p>
                                    <p>Watering Amount: {active.WateringAmount} ml</p>
                                    <p>Watering Nozzle Height: {active.height / 10} cm</p>
                                    <p>Total Water Consumption: {active.total_water_consumption} ml</p>
                                    <p className="active">Job status: {active.job_status}</p>
                                  </>
                              )}
                              <div className="button-group">
                                <button className="execute-button" onClick={() => handleExecuteJob(active._id)}>Execute
                                </button>
                                <button className="modify-button" onClick={() => handleEditJob(active)}>Modify</button>
                                <button className="delete-button" onClick={() => handleDeleteJob(active._id)}>Delete</button>
                              </div>
                            </div>)}
                      </div>
                  )}
                </div>
            )}
            <div
                className={darkmode ? `main-contentdark ${!showSidebar ? 'expanded' : ''}` : `main-content ${!showSidebar ? 'expanded' : ''}`}>
              <div className="field-selector-container">
                <FieldSelector workingArea={workingArea} setWorkingArea={setWorkingArea}/>
              </div>
              <div className="farmbot-status-container">
                <StatusDisplay/>
              </div>
            </div>
            <div className={darkmode ? "right-sidebardark" : "right-sidebar"}>
              {(showForm || showWForm) && (
                  <div className={darkmode ? "form-containerdark" : "form-container"}>
                    <Formik
                        innerRef={formikRef}
                        initialValues={{
                          jobType: currentJob ? currentJob.jobType : showWForm ? 'Watering' : 'Seeding',
                          seedType: currentJob ? currentJob.seedType : '',
                          seedingDate: currentJob ? new Date(currentJob.seedingDate) : seedingDate,
                          seedingDepth: currentJob ? currentJob.seedingDepth : 4,
                          plantDistance: currentJob ? currentJob.plantDistance : 120,
                          x0: currentJob ? currentJob.x0 : workingArea.x0,
                          y0: currentJob ? currentJob.y0 : workingArea.y0,
                          x1: currentJob ? currentJob.x1 : workingArea.x1,
                          y1: currentJob ? currentJob.y1 : workingArea.y1,
                          wateringDate: currentJob ? new Date(currentJob.wateringDate) : wateringDate,
                          Interval: currentJob ? currentJob.Interval : 3,
                          WateringAmount: currentJob ? currentJob.WateringAmount : 60,
                          height: currentJob ? currentJob.height : 10,
                          user_id: user_id,
                          job_status: "inactive",
                          name: name,
                          total_water_consumption : currentJob ? currentJob.total_water_consumption : 60,
                        }}
                        validationSchema={currentJob && currentJob.jobType === 'Watering' ? wateringJobSchema : seedingJobSchema}
                        onSubmit={handleSubmitJob}
                    >
                      {({ isSubmitting, setFieldValue }) => (
                          <Form className={darkmode ? "formdark" : ""}>
                            <h2>{currentJob ? `Edit ${currentJob.jobType} Job` : showWForm ? 'Create Watering Job' : 'Create Seeding Job'}</h2>
                            {showWForm ? (
                                <>
                                  <div>
                                    <label>Water Type</label>
                                    <Field as="select" name="seedType">
                                      <option value="">Select Water Type</option>
                                      <option value="Lettuce">Lettuce</option>
                                      <option value="Raddish">Raddish</option>
                                      <option value="Carrot">Carrot</option>
                                    </Field>
                                    <ErrorMessage name="seedType" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Schedule Date and Time</label>
                                    <DatePicker
                                        selected={wateringDate}
                                        onChange={(date) => {
                                          setWateringDate(date);
                                          setFieldValue('wateringDate', date);
                                        }}
                                        name="wateringDate"
                                        dateFormat="dd.MM.yyyy HH:mm"
                                        className="date-picker-input"
                                        showTimeSelect
                                        timeIntervals={1}
                                        timeFormat="HH:mm"
                                        timeCaption="time"
                                    />
                                    <ErrorMessage name="wateringDate" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Interval [h]</label>
                                    <Field type="number" name="Interval" />
                                    <ErrorMessage name="Interval" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Watering Amount [ml]</label>
                                    <Field type="number" name="WateringAmount" />
                                    <ErrorMessage name="WateringAmount" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Watering Nozzle Height [cm]</label>
                                    <Field type="number" name="height" />
                                    <ErrorMessage name="height" component="div" className="error" />
                                  </div>
                                </>
                            ) : (
                                <>
                                  <div>
                                    <label>Seed Type</label>
                                    <Field as="select" name="seedType">
                                      <option value="">Select Seed Type</option>
                                      <option value="Lettuce">Lettuce</option>
                                      <option value="Raddish">Raddish</option>
                                      <option value="Carrot">Carrot</option>
                                    </Field>
                                    <ErrorMessage name="seedType" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Seeding Date and Time</label>
                                    <DatePicker
                                        selected={seedingDate}
                                        onChange={(date) => {
                                          setSeedingDate(date);
                                          setFieldValue('seedingDate', date);
                                        }}
                                        name="seedingDate"
                                        dateFormat="dd.MM.yyyy HH:mm"
                                        className="date-picker-input"
                                        showTimeSelect
                                        timeIntervals={1}
                                        timeFormat="HH:mm"
                                        timeCaption="time"
                                    />
                                    <ErrorMessage name="seedingDate" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Seeding Depth [mm]</label>
                                    <Field type="number" name="seedingDepth" />
                                    <ErrorMessage name="seedingDepth" component="div" className="error" />
                                  </div>
                                  <div>
                                    <label>Plant Distance [mm]</label>
                                    <Field type="number" name="plantDistance" />
                                    <ErrorMessage name="plantDistance" component="div" className="error" />
                                  </div>
                                  <div className="hidden">
                                    <div>
                                      <label>X0 [cm]</label>
                                      <Field type="number" name="x0" />
                                      <ErrorMessage name="x0" component="div" className="error" />
                                    </div>
                                    <div>
                                      <label>Y0 [cm]</label>
                                      <Field type="number" name="y0" />
                                      <ErrorMessage name="y0" component="div" className="error" />
                                    </div>
                                    <div>
                                      <label>X1 [cm]</label>
                                      <Field type="number" name="x1" />
                                      <ErrorMessage name="x1" component="div" className="error" />
                                    </div>
                                    <div>
                                      <label>Y1 [cm]</label>
                                      <Field type="number" name="y1" />
                                      <ErrorMessage name="y1" component="div" className="error" />
                                    </div>
                                  </div>
                                </>
                            )}
                            <button type="submit" disabled={isSubmitting}>
                              {currentJob ? 'Update' : 'Create'}
                            </button>
                          </Form>
                      )}
                    </Formik>
                  </div>
              )}
            </div>
          </div>
        </div>
      </>
  );
};

export default Dashboard;
