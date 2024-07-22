import React, { useEffect, useRef, useState } from 'react';
import '../styles/FieldSelector.css';

const FieldSelector = ({ workingArea, setWorkingArea }) => {
  const canvasRef = useRef(null);
  const [plantedSeeds, setPlantedSeeds] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [startPosition, setStartPosition] = useState({ x: 0, y: 0 });
  const seedSpacingRadius = 20; // Adjust the radius as needed
  const [temporarySeeds, setTemporarySeeds] = useState([]);

  const fetchPlantedSeeds = () => {
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      console.log('WebSocket connection opened');
      socket.send(JSON.stringify({ action: 'get-planted-seeds' }));
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      //console.log('Message received from WebSocket:', message);
      if (message.action === 'planted-seeds-data') {
        //console.log('Planted Seeds Data:', message.data);
        setPlantedSeeds(message.data);
      }
      socket.close();  // Close the socket after receiving the message
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed', event);
    };
  };

  useEffect(() => {
    fetchPlantedSeeds(); // Fetch immediately on component mount
    const intervalId = setInterval(fetchPlantedSeeds, 10000); // Fetch every 10 seconds
    return () => clearInterval(intervalId); // Cleanup on unmount
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    drawGrid(context);
    drawSelectedArea(context, workingArea);
    drawPlantedSeeds(context, plantedSeeds);
    drawTemporarySeeds(context, temporarySeeds);
  }, [workingArea, plantedSeeds, temporarySeeds]);

  const drawGrid = (context) => {
    context.clearRect(0, 0, 870, 386);
    context.font = 'bold 10px Arial';
    context.fillStyle = 'black';
    context.strokeStyle = '#ddd';
    context.lineWidth = 1;

    for (let x = 0; x <= 870; x += 87) {
      context.beginPath();
      context.moveTo(x, 0);
      context.lineTo(x, 386);
      context.stroke();
      context.fillText(Math.ceil(x * (2700 / 870)), x, 386); // Adjusted y position for x coordinates
    }

// Explicitly add the final value to ensure 2700 is displayed
    context.fillText(2700, 845, 386);
    let maxYValue = 1200;
    let canvasHeight = 386;
    let steps = 10; // Number of steps for the y-axis
    let stepY = canvasHeight / steps; // Adjusting the step size

    for (let i = 0; i <= steps; i++) {
      let y = canvasHeight - (i * stepY);
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(870, y);
      context.stroke();
      context.fillText(Math.ceil((maxYValue / steps) * i), 0, y + 10);
    }



    context.strokeStyle = '#000';
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(0, 0);
    context.lineTo(0, 386);
    context.stroke();
    context.beginPath();
    context.moveTo(0, 0);
    context.lineTo(870, 0);
    context.stroke();
  };

  const drawSelectedArea = (context, area) => {
    context.fillStyle = 'rgba(173, 216, 230, 0.5)';
    context.fillRect(area.x0, 386 - area.y1, area.x1 - area.x0, area.y1 - area.y0);
  };

  const drawPlantedSeeds = (context, seeds) => {
    //console.log('Drawing planted seeds:', seeds); // Debugging line

    const images = {
      lettuce: new Image(),
      carrot: new Image(),
      raddish: new Image(),
    };

    images.lettuce.src = process.env.PUBLIC_URL + '/Cabbage.ico'; // Replace with the path to your lettuce icon
    images.carrot.src = process.env.PUBLIC_URL + '/Carrot.png'; // Replace with the path to your carrot icon
    images.raddish.src = process.env.PUBLIC_URL + '/Raddish.png'; // Replace with the path to your raddish icon

    const drawIcon = () => {
      const canvasHeight = context.canvas.height; // Get the canvas height
      if (seeds.length < 2) {
        console.error("Insufficient seeds to calculate distance");
        return;
      }

      let seedoe = seeds[0];
      let seedto = seeds[1];

      if (!seedoe || !seedto) {
        console.error("Seed elements are undefined", seeds);
        return;
      }

      let seedoe_x = seedoe.x;
      let seedoe_y = seedoe.y;
      let seedto_x = seedto.x;
      let seedto_y = seedto.y;

      let distance = Math.sqrt(Math.pow((seedto_x - seedoe_x), 2) + Math.pow((seedto_y - seedoe_y), 2))/20;
      //console.log(distance);

      seeds.forEach(seed => {
        if (!seed) {
          console.error("Undefined seed in array", seeds);
          return;
        }
        //console.log('Drawing seed at:', seed); // Debugging line
        const icon = images[seed.seedType.toLowerCase()];
        if (icon) {
          const flippedY = canvasHeight - seed.y;
          context.drawImage(icon, seed.x - 12, flippedY - 12, 24, 24);
          context.beginPath();
          context.arc(seed.x, flippedY, seed.plantDistance/6, 0, 2 * Math.PI, false);
          context.fillStyle = 'rgba(255,216,216,0.2)'; // Light red fill
          context.fill();
          context.lineWidth = 1;
          context.strokeStyle = 'rgba(58,2,2,0.3)'; // Dark red stroke
          context.stroke(); // Draw the circle
        } else {
          console.error("Icon not found for seed type", seed.seedType);
        }
      });
    };

    // Ensure all images are loaded before drawing
    const allImagesLoaded = Object.values(images).every(img => img.complete);
    if (allImagesLoaded) {
      drawIcon();
    } else {
      Object.values(images).forEach(img => {
        img.onload = () => {
          if (Object.values(images).every(image => image.complete)) {
            drawIcon();
          }
        };
      });
    }
  };

  const handleMouseDown = (e) => {
    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = rect.bottom - e.clientY; // Adjusted y calculation
    setStartPosition({ x, y });
    setIsDragging(true);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    sendAreaToServer(workingArea);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = rect.bottom - e.clientY; // Adjusted y calculation
    const selectedArea = {
      x0: Math.min(startPosition.x, x),
      y0: Math.min(startPosition.y, y),
      x1: Math.max(startPosition.x, x),
      y1: Math.max(startPosition.y, y),
    };

    setWorkingArea(selectedArea);
  };

  const drawTemporarySeeds = (context, seeds) => {
    const image = new Image();
    image.src = process.env.PUBLIC_URL + '/Cabbage.ico'; // Replace with the path to your lettuce icon

    const drawIcon = () => {
      const canvasHeight = context.canvas.height;
      context.globalAlpha = 0.60; // Set opacity to 50%
      seeds.forEach(seed => {
        const flippedY = canvasHeight - seed.y;
        context.drawImage(image, seed.x - 12, flippedY - 12, 24, 24);
      });
      context.globalAlpha = 1.0; // Reset opacity after drawing
    };

    if (image.complete) {
      drawIcon();
    } else {
      image.onload = drawIcon;
    }
  };


  const sendAreaToServer = (selectedArea) => {
    const areaWithPlantDistance = {
      ...selectedArea,
      x0: Math.ceil(selectedArea.x0 * (2700 / 870)),
      x1: Math.ceil(Math.min(selectedArea.x1, 870) * (2700 / 870)),
      y0: Math.ceil(selectedArea.y0 * (2700 / 870)),
      y1: Math.ceil(Math.min(selectedArea.y1, 435) * (2700 / 870)),
      plantDistance: 120 ,
    };
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      console.log('WebSocket connection opened');
      socket.send(JSON.stringify({ action: 'send-area', area: areaWithPlantDistance }));
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.action === 'calculated-plant-positions') {
        setTemporarySeeds(message.data);
      }
      socket.close();  // Close the socket after receiving the message
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed', event);
    };
  };
  return (
      <div
          className="field-selector"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
      >
        <canvas
            ref={canvasRef}
            width="870"
            height="386"
            style={{ border: '1px solid #000000', backgroundColor: 'lightbrown' }}
        ></canvas>
      </div>
  );
};

export default FieldSelector;
