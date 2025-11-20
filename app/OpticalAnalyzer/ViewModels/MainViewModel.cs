using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LiveChartsCore;
using LiveChartsCore.Defaults;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using Microsoft.Win32;
using OpticalAnalyzer.Models;
using OpticalAnalyzer.Services;
using SkiaSharp;

namespace OpticalAnalyzer.ViewModels
{
    /// <summary>
    /// Main ViewModel for the Optical Spectrum Analyzer application.
    /// Handles data loading, analysis, and UI state management.
    /// </summary>
    public partial class MainViewModel : ObservableObject
    {
        private readonly ISpectrumDataService _dataService;
        private readonly IQualityAnalysisService _analysisService;
        private readonly IReportService _reportService;

        private List<SpectrumData> _loadedSpectra = new();
        private List<QualityAnalysisResult> _analysisResults = new();

        [ObservableProperty]
        private string _statusMessage = "Ready. Load a CSV file to begin analysis.";

        [ObservableProperty]
        private bool _isDataLoaded = false;

        [ObservableProperty]
        private bool _isAnalysisComplete = false;

        [ObservableProperty]
        private string _loadedFileName = "";

        [ObservableProperty]
        private int _totalSamples = 0;

        [ObservableProperty]
        private int _totalMaterials = 0;

        [ObservableProperty]
        private ObservableCollection<string> _sampleIds = new();

        [ObservableProperty]
        private string? _selectedSampleId;

        [ObservableProperty]
        private SpectrumData? _currentSpectrum;

        [ObservableProperty]
        private QualityAnalysisResult? _currentResult;

        // Chart data
        [ObservableProperty]
        private ISeries[] _spectrumSeries = Array.Empty<ISeries>();

        [ObservableProperty]
        private Axis[] _xAxes = { new Axis { Name = "Wavelength (nm)", MinLimit = 200, MaxLimit = 2500 } };

        [ObservableProperty]
        private Axis[] _yAxes = { new Axis { Name = "Transmission (%)", MinLimit = 0, MaxLimit = 105 } };

        // Summary statistics
        [ObservableProperty]
        private int _passCount = 0;

        [ObservableProperty]
        private int _failCount = 0;

        [ObservableProperty]
        private double _passRate = 0;

        [ObservableProperty]
        private int _excellentCount = 0;

        [ObservableProperty]
        private int _goodCount = 0;

        [ObservableProperty]
        private int _fairCount = 0;

        [ObservableProperty]
        private int _poorCount = 0;

        public MainViewModel(
            ISpectrumDataService dataService,
            IQualityAnalysisService analysisService,
            IReportService reportService)
        {
            _dataService = dataService;
            _analysisService = analysisService;
            _reportService = reportService;
        }

        // Default constructor for design-time
        public MainViewModel() : this(
            new SpectrumDataService(),
            new QualityAnalysisService(),
            new ReportService())
        { }

        [RelayCommand]
        private async Task LoadDataAsync()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "CSV Files (*.csv)|*.csv|All Files (*.*)|*.*",
                Title = "Select Spectroscopy Data File"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    StatusMessage = "Loading data...";
                    
                    _loadedSpectra = await _dataService.LoadFromCsvAsync(dialog.FileName);
                    
                    LoadedFileName = System.IO.Path.GetFileName(dialog.FileName);
                    TotalSamples = _loadedSpectra.Count;
                    TotalMaterials = _dataService.GetUniqueMaterials(_loadedSpectra).Count;
                    
                    SampleIds = new ObservableCollection<string>(
                        _dataService.GetUniqueSampleIds(_loadedSpectra));
                    
                    IsDataLoaded = true;
                    IsAnalysisComplete = false;
                    StatusMessage = $"Loaded {TotalSamples} samples from {LoadedFileName}";

                    // Auto-select first sample
                    if (SampleIds.Any())
                    {
                        SelectedSampleId = SampleIds.First();
                    }
                }
                catch (Exception ex)
                {
                    StatusMessage = $"Error loading file: {ex.Message}";
                    MessageBox.Show($"Failed to load file:\n{ex.Message}", "Error", 
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        [RelayCommand]
        private void RunAnalysis()
        {
            if (!IsDataLoaded || !_loadedSpectra.Any())
            {
                StatusMessage = "No data loaded. Please load a CSV file first.";
                return;
            }

            try
            {
                StatusMessage = "Running quality analysis...";
                
                _analysisResults = _analysisService.AnalyzeMultiple(_loadedSpectra);
                
                // Update summary statistics
                PassCount = _analysisResults.Count(r => r.PassedQC);
                FailCount = _analysisResults.Count - PassCount;
                PassRate = TotalSamples > 0 ? (PassCount * 100.0 / TotalSamples) : 0;
                
                ExcellentCount = _analysisResults.Count(r => r.Grade == QualityGrade.Excellent);
                GoodCount = _analysisResults.Count(r => r.Grade == QualityGrade.Good);
                FairCount = _analysisResults.Count(r => r.Grade == QualityGrade.Fair);
                PoorCount = _analysisResults.Count(r => r.Grade == QualityGrade.Poor);
                
                IsAnalysisComplete = true;
                StatusMessage = $"Analysis complete. Pass rate: {PassRate:F1}%";

                // Update current sample result
                UpdateSelectedSample();
            }
            catch (Exception ex)
            {
                StatusMessage = $"Analysis error: {ex.Message}";
            }
        }

        partial void OnSelectedSampleIdChanged(string? value)
        {
            UpdateSelectedSample();
        }

        private void UpdateSelectedSample()
        {
            if (string.IsNullOrEmpty(SelectedSampleId) || !_loadedSpectra.Any())
                return;

            CurrentSpectrum = _dataService.GetSampleById(_loadedSpectra, SelectedSampleId);
            
            if (CurrentSpectrum != null)
            {
                UpdateChart();
                
                if (IsAnalysisComplete)
                {
                    CurrentResult = _analysisResults.FirstOrDefault(r => r.SampleId == SelectedSampleId);
                }
            }
        }

        private void UpdateChart()
        {
            if (CurrentSpectrum == null || !CurrentSpectrum.DataPoints.Any())
                return;

            var values = CurrentSpectrum.DataPoints
                .Select(p => new ObservablePoint(p.WavelengthNm, p.TransmissionPercent))
                .ToArray();

            var color = CurrentResult?.Grade switch
            {
                QualityGrade.Excellent => SKColors.Green,
                QualityGrade.Good => SKColors.DodgerBlue,
                QualityGrade.Fair => SKColors.Orange,
                QualityGrade.Poor => SKColors.Red,
                _ => SKColors.SteelBlue
            };

            SpectrumSeries = new ISeries[]
            {
                new LineSeries<ObservablePoint>
                {
                    Values = values,
                    Fill = null,
                    GeometrySize = 0,
                    Stroke = new SolidColorPaint(color) { StrokeThickness = 2 },
                    Name = CurrentSpectrum.MaterialType
                }
            };

            // Update axes
            XAxes = new Axis[]
            {
                new Axis 
                { 
                    Name = "Wavelength (nm)",
                    MinLimit = CurrentSpectrum.MinWavelength,
                    MaxLimit = CurrentSpectrum.MaxWavelength
                }
            };
        }

        [RelayCommand]
        private void ExportReport()
        {
            if (!IsAnalysisComplete)
            {
                MessageBox.Show("Please run analysis first.", "Info", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dialog = new SaveFileDialog
            {
                Filter = "Text Files (*.txt)|*.txt|CSV Files (*.csv)|*.csv",
                Title = "Export Report",
                FileName = $"QC_Report_{DateTime.Now:yyyyMMdd_HHmmss}"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    if (dialog.FileName.EndsWith(".csv"))
                    {
                        _reportService.ExportToCsv(_analysisResults, dialog.FileName);
                    }
                    else
                    {
                        var report = _reportService.GenerateTextReport(_analysisResults);
                        System.IO.File.WriteAllText(dialog.FileName, report);
                    }
                    
                    StatusMessage = $"Report exported to {System.IO.Path.GetFileName(dialog.FileName)}";
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Export failed:\n{ex.Message}", "Error", 
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        [RelayCommand]
        private void ShowSampleReport()
        {
            if (CurrentResult == null)
            {
                MessageBox.Show("No sample selected or analysis not complete.", "Info", 
                    MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var report = _reportService.GenerateSampleReport(CurrentResult);
            MessageBox.Show(report, $"Sample Report: {CurrentResult.SampleId}", 
                MessageBoxButton.OK, MessageBoxImage.None);
        }
    }
}