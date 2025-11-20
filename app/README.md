# Optical Analyzer - Desktop Application

A Windows desktop application (WPF/.NET 6) for analyzing optical transmission spectra and performing quality control classification.

> **⚠️ Windows Only:** This WPF application requires Windows to build and run. The source code can be viewed on any platform.

## Features

- **Load CSV Data**: Import spectroscopy data from CSV files
- **Interactive Spectrum Viewer**: Zoomable chart with wavelength/transmission display
- **Quality Analysis**: Automatic quality grading (Excellent/Good/Fair/Poor)
- **Defect Detection**: Identifies scratches, impurities, and coating defects
- **Report Generation**: Export QC reports in TXT or CSV format
- **Multi-Sample Support**: Analyze batches of samples from a single file

## Requirements

- Windows 10/11
- .NET 6.0 Runtime or later
- Visual Studio 2022 (for development)

## Building from Source (Windows)

```bash
# Navigate to app directory
cd app

# Restore NuGet packages
dotnet restore

# Build the project
dotnet build

# Run the application
dotnet run --project OpticalAnalyzer
```

## Usage

1. **Load Data**: Click "Load Data" and select a CSV file with spectroscopy measurements
2. **Select Sample**: Choose a sample from the left panel to view its spectrum
3. **Run Analysis**: Click "Run Analysis" to perform quality classification on all samples
4. **View Results**: See quality grade, transmission metrics, and defect information
5. **Export Report**: Click "Export Report" to save results as TXT or CSV

## Expected CSV Format

```csv
wavelength_nm,transmission_percent,material_type,sample_id,thickness_mm
200,45.2,Fused Silica (SiO₂),sample_001,2.0
202,48.1,Fused Silica (SiO₂),sample_001,2.0
...
```

## Project Structure

```
OpticalAnalyzer/
├── Models/
│   └── SpectrumModels.cs      # Data models
├── Services/
│   ├── SpectrumDataService.cs  # CSV loading
│   ├── QualityAnalysisService.cs # Analysis logic
│   └── ReportService.cs        # Report generation
├── ViewModels/
│   └── MainViewModel.cs        # MVVM ViewModel
├── Views/
│   ├── MainWindow.xaml         # Main UI
│   └── MainWindow.xaml.cs      # Code-behind
├── App.xaml                    # Application resources
└── App.xaml.cs                 # Application entry point
```

## Dependencies

- **CsvHelper** - CSV parsing
- **LiveChartsCore** - Interactive charting
- **CommunityToolkit.Mvvm** - MVVM framework
- **Microsoft.Extensions.DependencyInjection** - Dependency injection

## Quality Grading Criteria

| Grade | Avg Visible Transmission | Color |
|-------|-------------------------|-------|
| Excellent | ≥90% | Green |
| Good | 80-90% | Blue |
| Fair | 70-80% | Orange |
| Poor | <70% | Red |

## Author

Kuldeep Choksi