// Analytics.jsx
import React, { useEffect, useState } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';  // Importing multiple chart types
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, PointElement, LineElement, ArcElement } from 'chart.js';  // Import missing components

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, PointElement, LineElement, ArcElement);  // Register PointElement and LineElement


// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Analytics = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:5000/getLog'); // Replace with actual data source
        console.log('Analytics data:', response.data);
        setData(JSON.parse(response.data));
      } catch (error) {
        console.error('Error fetching analytics data:', error);
      }
    };

    fetchData();
  }, []);

  // Generate chart data based on fetched data
  const getLineChartData = (showRecentOnly = false) => {
    if (!data || !data.results) return {};
  
    // Create arrays to store time data for each attribute over the results
    const classifierTimes = [];
    const retrieverTimes = [];
    const summarizerTimes = [];
  
    // Determine the data range (all results or just the most recent one)
    const resultsToDisplay = showRecentOnly ? [data.results[data.results.length - 1]] : data.results;
    console.log("Results to display: ", resultsToDisplay)
  
    // Loop over the selected results to collect times for each attribute
    resultsToDisplay.forEach((result, index) => {
      classifierTimes.push(result.classifier.time);
      retrieverTimes.push(result.retriever.time_taken);
      summarizerTimes.push(result.summarizer.time);
    });
  
    return {
      labels: showRecentOnly
        ? ['Most Recent Result']  // Label for a single result
        : Array.from({ length: resultsToDisplay.length }, (_, i) => `Result ${i + 1}`),  // Label for each result
  
      datasets: [
        {
          label: 'Classifier Time',
          data: classifierTimes,
          borderColor: 'rgba(75,192,192,1)',
          fill: false,
          pointRadius: 5,
          tension: 0.3,
        },
        {
          label: 'Retriever Time',
          data: retrieverTimes,
          borderColor: 'rgba(255,99,132,1)',
          fill: false,
          pointRadius: 5,
          tension: 0.3,
        },
        {
          label: 'Summarizer Time',
          data: summarizerTimes,
          borderColor: 'rgba(54,162,235,1)',
          fill: false,
          pointRadius: 5,
          tension: 0.3,
        },
      ],
    };
  };
  
  const simpleLinePlot = () =>{
    
    if (!data) return {};

    // Extracting the time values from classifier, retriever, and summarizer
    const recent_item = data.results[data.results.length - 1]
    const times = {
      classifier: recent_item.classifier.time,
      retriever: recent_item.retriever.time_taken,
      summarizer: recent_item.summarizer.time,
    };
  
    return {
      labels: ['Classifier', 'Retriever', 'Summarizer'],  // Use keys as labels for each category
      datasets: [
        {
          label: 'Processing Time',
          data: [times.classifier, times.retriever, times.summarizer], // Using the extracted time values
          borderColor: 'rgba(75,192,192,1)',
          fill: false,
        },
      ],
    };
  }

  const getSimpleBarChartData = () => {
    if (!data) return {};
    const recent_item = data.results[data.results.length - 1]
    const topics = (recent_item.classifier.topics)
    return {
      labels: topics,  // Assuming data has categories
      datasets: [
        {
          label: 'Category Distribution',
          data: recent_item.classifier.probability_values,  // Assuming data.categoryCounts contains the number of occurrences per category
          backgroundColor: 'rgba(255,99,132,0.2)',
          borderColor: 'rgba(255,99,132,1)',
          borderWidth: 1,
        },
      ],
    };
  };

  const getBarChartData = () => {
    if (!data || !data.results || !data.results.length) return {};
  
    // Get all unique topics across all results
    const allCategories = [...new Set(data.results.flatMap(result => result.classifier.topics))];
  
    // Initialize an object to store the total probabilities and count for each category
    const categoryProbabilities = allCategories.reduce((acc, category) => {
      acc[category] = { total: 0, count: 0 };
      return acc;
    }, {});
  
    // Aggregate probabilities for each category
    data.results.forEach(result => {
      result.classifier.topics.forEach((topic, index) => {
        if (categoryProbabilities[topic]) {
          categoryProbabilities[topic].total += result.classifier.probability_values[index];
          categoryProbabilities[topic].count += 1;
        }
      });
    });
  
    // Compute average probabilities for each category
    const averageProbabilities = allCategories.map(
      category => categoryProbabilities[category].total / categoryProbabilities[category].count
    );
  
    return {
      labels: allCategories, // Categories (Topics)
      datasets: [
        {
          label: 'Average Probability',
          data: averageProbabilities, // Average probabilities for each category
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };
  };
  
  
//   const getPieChartData = () => {
//     if (!data) return {};
//     return {
//       labels: data.pieLabels,  // Assuming data.pieLabels contains pie chart segments' labels
//       datasets: [
//         {
//           data: data.pieData,  // Assuming data.pieData contains the values for each pie segment
//           backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
//         },
//       ],
//     };
//   };

const getTopicDistributionData = () => {
    if (!data || !data.results || !data.results.length) return {};
  
    // Aggregate counts for each topic
    const topicCounts = {};
    data.results.forEach(result => {
      result.retriever.Response.results.forEach(doc => {
        topicCounts[doc.topic] = (topicCounts[doc.topic] || 0) + 1;
      });
    });
  
    // Extract data for the pie chart
    const topics = Object.keys(topicCounts);
    const counts = Object.values(topicCounts);
  
    return {
      labels: topics, // Topic names
      datasets: [
        {
          data: counts, // Document count per topic
          backgroundColor: topics.map((_, index) =>
            `hsl(${(index * 360) / topics.length}, 70%, 50%)`
          ), // Dynamic colors for each topic
          hoverOffset: 4,
        },
      ],
    };
  };


  const getScoreContributionData = () => {
    if (!data || !data.results || !data.results.length) return {};
  
    // Aggregate scores for each topic
    const topicScores = {};
    const topicCounts = {};
    data.results.forEach(result => {
      result.retriever.Response.results.forEach(doc => {
        topicScores[doc.topic] = (topicScores[doc.topic] || 0) + doc.score;
        topicCounts[doc.topic] = (topicCounts[doc.topic] || 0) + 1;
      });
    });
  
    // Extract data for the pie chart
    const topics = Object.keys(topicScores);
    const scaledScores = topics.map(topic => 
        Math.log(1 + topicScores[topic] / topicCounts[topic])
      );
    
      
    // const scores = Object.values(topicScores);

    // const averageScores = topics.map(topic => topicScores[topic] / topicCounts[topic]);
    
  
    return {
      labels: topics, // Topic names
      datasets: [
        {
          data: scaledScores, // Total score per topic
          backgroundColor: topics.map((_, index) =>
            `hsl(${(index * 360) / topics.length}, 70%, 50%)`
          ), // Dynamic colors for each topic
          hoverOffset: 4,
        //   borderColor: 'rgba(255,99,132,1)',
        //   borderWidth: 0
        },
      ],
    };
  };

  const getSimpleScoreContributionData = () => {
    if (!data || !data.results || !data.results.length) return {};
  
    // Get the most recent result
    const recent_result = data.results[data.results.length - 1];
  
    // Aggregate scores for each topic in the recent result
    const topicScores = {};
    recent_result.retriever.Response.results.forEach(doc => {
      topicScores[doc.topic] = (topicScores[doc.topic] || 0) + doc.score;
    });
  
    // Extract data for the pie chart
    const topics = Object.keys(topicScores);
    const scores = Object.values(topicScores);
  
    return {
      labels: topics, // Topic names
      datasets: [
        {
          data: scores, // Total score per topic
          backgroundColor: topics.map((_, index) =>
            `hsl(${(index * 360) / topics.length}, 70%, 50%)`
          ), // Dynamic colors for each topic
          hoverOffset: 4,
        },
      ],
    };
  };
  

  return (
    <div>
    {data ? (
        <>
        <div style={{ height: '100vh', overflowY: 'auto' }}>
          {/* Header for the first container */}
          <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>
            Analytics Across All Queries Until Now
          </h2>
      
          {/* Charts container */}
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '20px', flexWrap: 'wrap' }}>
            {/* Line Chart */}
            <div style={{ width: '30%' }}>
              <h3>Responses Over Time</h3>
              <Line data={getLineChartData(false)} />
            </div>
      
            {/* Bar Chart */}
            <div style={{ width: '30%' }}>
              <h3>Category Distribution</h3>
              <Bar data={getBarChartData()} />
            </div>
      
            {/* Pie Chart */}
            <div style={{ width: '30%' }}>
              <h3>Score Distribution</h3>
              <Pie data={getScoreContributionData()} />
            </div>
          </div>
      
          {/* Second Container Header */}
          <h2 style={{ textAlign: 'center', margin: '30px 0 10px' }}>
            Recent Query Stats
          </h2>
      
          {/* Recent Query Stats Section */}
          <div style={{ marginTop: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '20px' }}>
              <div style={{ width: '30%' }}>
                <h3>Responses Over Time (Recent Query)</h3>
                <Line data={simpleLinePlot()} />
              </div>
              <div style={{ width: '30%' }}>
                <h3>Category Distribution</h3>
                <Bar data={getSimpleBarChartData()} />
              </div>
              <div style={{ width: '30%' }}>
                <h3>Retrieved Score Contribution</h3>
                <Pie data={getSimpleScoreContributionData()} />
              </div>
            </div>
          </div>
        </div>
      </>
      
      ) : (
        <p>Loading analytics...</p>
      )}
    </div>
  );
};

export default Analytics;
