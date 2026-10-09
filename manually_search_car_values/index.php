<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get JSON input from the frontend
    $data = json_decode(file_get_contents('php://input'), true);

    $vin = escapeshellarg($data['vin']);
    $mileage = escapeshellarg($data['mileage']);
    $style = escapeshellarg($data['style']);

    // Explicitly use the Python binary from the virtual environment
    $pythonBinary = '/Applications/MAMP/htdocs/NEW_CAR/car_values/env/bin/python'; // Update this path
    $command = "$pythonBinary main.py $vin $mileage $style 2>&1";
    $output = [];
    exec($command, $output);

    // Return the result and progress logs as JSON
    header('Content-Type: application/json');
    echo json_encode(['result' => end($output), 'logs' => $output]);
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Car Appraisal Tool</title>
    <style>
    #progress {
        width: 100%;
        background-color: #f3f3f3;
    }

    #progress-bar {
        width: 0%;
        height: 30px;
        background-color: #4caf50;
        text-align: center;
        line-height: 30px;
        color: white;
    }

    .hide {
        display: none;
    }

    body {
        font-family: Arial, sans-serif;
        margin: 20px;
    }

    label {
        display: block;
        margin-bottom: 8px;
        font-weight: bold;
    }

    input {
        width: 100%;
        padding: 8px;
        margin-bottom: 15px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    button {
        padding: 10px 15px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    button:hover {
        background-color: #0056b3;
    }

    .output {
        margin-top: 20px;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        background-color: #f9f9f9;
    }
    </style>
</head>

<body>
    <h1>Car Appraisal Tool</h1>
    <form id="appraisalForm">
        <label for="vin">VIN:</label>
        <input type="text" id="vin" name="vin" required><br>

        <label for="mileage">Mileage:</label>
        <input type="text" id="mileage" name="mileage" required><br>

        <label for="style">Style:</label>
        <input type="text" id="style" name="style" required><br>

        <button type="button" onclick="runAppraisal()">Run Appraisal</button>
    </form>

    <h2>Progress:</h2>
    <div id="progress">
        <div id="progress-bar">0%</div>
    </div>

    <h2 class="hide">Logs:</h2>
    <pre class="hide" id="logs"></pre>

    <h2>Result:</h2>
    <div id="result"></div>

    <script>
    async function runAppraisal() {
        const vin = document.getElementById('vin').value;
        const mileage = document.getElementById('mileage').value;
        const style = document.getElementById('style').value;

        document.getElementById('progress-bar').style.width = "0%";
        document.getElementById('progress-bar').innerText = "0%";
        document.getElementById('logs').innerText = "";
        document.getElementById('result').innerText = "";

        const response = await fetch('index.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                vin,
                mileage,
                style
            }),
        });

        const data = await response.json();

        // Update logs and result
        const logs = data.logs.join('\n');
        document.getElementById('logs').innerText = logs;

        // Show result
        document.getElementById('result').innerText = data.result;

        // Update progress bar to 100%
        document.getElementById('progress-bar').style.width = "100%";
        document.getElementById('progress-bar').innerText = "Completed";
    }
    </script>
</body>

</html>