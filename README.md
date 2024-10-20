# CFTC Commitment of Traders Report

[![CI Pipeline](https://github.com/kustex/CFTC-COT-Report/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/kustex/CFTC-COT-Report/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/kustex/CFTC-COT-Report/actions/workflows/cd.yml/badge.svg?branch=main)](https://github.com/kustex/CFTC-COT-Report/actions/workflows/cd.yml)

## Overview

The **CFTC-COT-Report A** provides a weekly update dashboard with tables + visualizations of z-scores en related metrics for Futures positions in all major Macro asset classes. 

### Key Features:
- **Positioning Monitoring**: Track the changes in positioning of various sectors, industries, and macroeconomic indicators over a multiduration time-horizon. 
- **Visualization**: Barcharts and scatterplots are shown to visualize changes over time. 

## Project Structure

```plaintext
CFTC-COT-Report/
│
├── app_cftc.py               # Main Python script to run the app and display dashboard
├── cftc_analyser.py          # Main Python script to download zip-files and make calculations
├── cftc_data                 # Directory with zip files (downloaded from https://www.cftc.gov/)
├── metrics.yaml              # File with all the names which cftc_analyser.py will be looking for in the downloaded Excel-files. 
├── requirements.txt          # Python dependencies
└── README.md                 # This README file
```

## Installation

### 1. Clone the Repository

Clone the repository to your local machine and make it the current directory:

```bash
git clone https://github.com/kustex/CFTC-COT-Report.git
cd CFTC-COT-Report
```

### 2. Create & activate a virtual environment 
```bash
python -m venv venv
source venv/bin/activate 
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Running the App
```bash
python main.py
```

### 4. Access the App: Open your web browser and go to:
```arduino
http://127.0.0.1:5000/
```
