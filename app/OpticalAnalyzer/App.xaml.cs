using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using OpticalAnalyzer.Services;
using OpticalAnalyzer.ViewModels;

namespace OpticalAnalyzer
{
    /// <summary>
    /// Optical Spectrum Analyzer - Desktop Application
    /// 
    /// A WPF application for analyzing optical transmission spectra
    /// and performing quality control classification.
    /// 
    /// Author: Kuldeep Choksi
    /// </summary>
    public partial class App : Application
    {
        private ServiceProvider? _serviceProvider;

        public App()
        {
            var services = new ServiceCollection();
            ConfigureServices(services);
            _serviceProvider = services.BuildServiceProvider();
        }

        private void ConfigureServices(IServiceCollection services)
        {
            // Register services
            services.AddSingleton<ISpectrumDataService, SpectrumDataService>();
            services.AddSingleton<IQualityAnalysisService, QualityAnalysisService>();
            services.AddSingleton<IReportService, ReportService>();

            // Register ViewModels
            services.AddTransient<MainViewModel>();
            services.AddTransient<SpectrumViewModel>();
            services.AddTransient<QualityResultsViewModel>();
        }

        public T GetService<T>() where T : class
        {
            return _serviceProvider?.GetService<T>() 
                ?? throw new InvalidOperationException($"Service {typeof(T)} not found");
        }
    }
}