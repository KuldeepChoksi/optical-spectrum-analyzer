using System;
using System.Collections.Generic;
using System.Linq;
using OpticalAnalyzer.Models;

namespace OpticalAnalyzer.Services
{
    /// <summary>
    /// Service for performing quality analysis on spectrum data.
    /// Implements defect detection and quality classification based on ISO 10110.
    /// </summary>
    public interface IQualityAnalysisService
    {
        QualityAnalysisResult AnalyzeSpectrum(SpectrumData spectrum, double qcThreshold = 80.0);
        List<QualityAnalysisResult> AnalyzeMultiple(List<SpectrumData> spectra, double qcThreshold = 80.0);
        QualityGrade ClassifyGrade(double avgVisibleTransmission);
    }

    public class QualityAnalysisService : IQualityAnalysisService
    {
        // Wavelength ranges (nm)
        private const double VisibleMin = 400.0;
        private const double VisibleMax = 700.0;
        
        // Defect detection thresholds
        private const double DefectGradientThreshold = 0.5;  // %/nm
        private const double DefectDropThreshold = 10.0;     // % drop from local mean

        /// <summary>
        /// Perform complete quality analysis on a single spectrum.
        /// </summary>
        public QualityAnalysisResult AnalyzeSpectrum(SpectrumData spectrum, double qcThreshold = 80.0)
        {
            var result = new QualityAnalysisResult
            {
                SampleId = spectrum.SampleId,
                MaterialType = spectrum.MaterialType,
                AnalysisDate = DateTime.Now
            };

            if (spectrum.DataPoints.Count == 0)
            {
                result.Notes.Add("No data points in spectrum");
                result.Grade = QualityGrade.Poor;
                result.PassedQC = false;
                return result;
            }

            var dataPoints = spectrum.DataPoints.OrderBy(p => p.WavelengthNm).ToList();
            var wavelengths = dataPoints.Select(p => p.WavelengthNm).ToArray();
            var transmissions = dataPoints.Select(p => p.TransmissionPercent).ToArray();

            // Peak transmission
            result.PeakTransmission = transmissions.Max();

            // Average transmission in visible range
            var visiblePoints = dataPoints
                .Where(p => p.WavelengthNm >= VisibleMin && p.WavelengthNm <= VisibleMax)
                .ToList();

            if (visiblePoints.Any())
            {
                result.AvgVisibleTransmission = visiblePoints.Average(p => p.TransmissionPercent);
            }
            else
            {
                result.AvgVisibleTransmission = transmissions.Average();
                result.Notes.Add("Visible range not covered - using full spectrum average");
            }

            // Full spectrum average
            result.AvgFullSpectrumTransmission = transmissions.Average();

            // Transmission bandwidth (where T > 80%)
            result.TransmissionBandwidthNm = CalculateBandwidth(dataPoints, 80.0);

            // Uniformity score (inverse of coefficient of variation)
            if (visiblePoints.Any())
            {
                var mean = visiblePoints.Average(p => p.TransmissionPercent);
                var stdDev = Math.Sqrt(visiblePoints.Average(p => Math.Pow(p.TransmissionPercent - mean, 2)));
                var cv = mean > 0 ? stdDev / mean : 1.0;
                result.UniformityScore = Math.Max(0, (1 - cv)) * 100;
            }

            // Defect detection
            result.Defects = DetectDefects(dataPoints);
            result.DefectCount = result.Defects.Count;

            if (result.DefectCount > 0)
            {
                result.Notes.Add($"Detected {result.DefectCount} potential defect(s)");
            }

            // Quality grade classification
            result.Grade = ClassifyGrade(result.AvgVisibleTransmission);

            // Pass/Fail determination
            result.PassedQC = result.AvgVisibleTransmission >= qcThreshold && result.DefectCount == 0;

            if (!result.PassedQC)
            {
                if (result.AvgVisibleTransmission < qcThreshold)
                {
                    result.Notes.Add($"Below QC threshold ({result.AvgVisibleTransmission:F1}% < {qcThreshold}%)");
                }
                if (result.DefectCount > 0)
                {
                    result.Notes.Add("Failed due to detected defects");
                }
            }

            return result;
        }

        /// <summary>
        /// Analyze multiple spectra.
        /// </summary>
        public List<QualityAnalysisResult> AnalyzeMultiple(List<SpectrumData> spectra, double qcThreshold = 80.0)
        {
            return spectra.Select(s => AnalyzeSpectrum(s, qcThreshold)).ToList();
        }

        /// <summary>
        /// Classify quality grade based on average visible transmission.
        /// </summary>
        public QualityGrade ClassifyGrade(double avgVisibleTransmission)
        {
            return avgVisibleTransmission switch
            {
                >= 90 => QualityGrade.Excellent,
                >= 80 => QualityGrade.Good,
                >= 70 => QualityGrade.Fair,
                _ => QualityGrade.Poor
            };
        }

        /// <summary>
        /// Calculate transmission bandwidth above a threshold.
        /// </summary>
        private double CalculateBandwidth(List<SpectrumDataPoint> dataPoints, double threshold)
        {
            var aboveThreshold = dataPoints.Where(p => p.TransmissionPercent >= threshold).ToList();
            
            if (!aboveThreshold.Any())
                return 0;

            return aboveThreshold.Max(p => p.WavelengthNm) - aboveThreshold.Min(p => p.WavelengthNm);
        }

        /// <summary>
        /// Detect defects in the spectrum based on sudden transmission drops.
        /// </summary>
        private List<DefectInfo> DetectDefects(List<SpectrumDataPoint> dataPoints)
        {
            var defects = new List<DefectInfo>();
            
            if (dataPoints.Count < 10)
                return defects;

            var wavelengths = dataPoints.Select(p => p.WavelengthNm).ToArray();
            var transmissions = dataPoints.Select(p => p.TransmissionPercent).ToArray();

            // Calculate gradient (first derivative)
            var gradients = new double[transmissions.Length - 1];
            for (int i = 0; i < gradients.Length; i++)
            {
                var dT = transmissions[i + 1] - transmissions[i];
                var dW = wavelengths[i + 1] - wavelengths[i];
                gradients[i] = dW > 0 ? dT / dW : 0;
            }

            // Detect sharp drops (large negative gradients)
            for (int i = 1; i < gradients.Length - 1; i++)
            {
                if (gradients[i] < -DefectGradientThreshold)
                {
                    // Check if this is a localized dip (defect) vs. edge absorption
                    var localMean = transmissions.Skip(Math.Max(0, i - 10))
                        .Take(20).Average();
                    
                    if (transmissions[i] < localMean - DefectDropThreshold)
                    {
                        defects.Add(new DefectInfo
                        {
                            WavelengthNm = wavelengths[i],
                            DefectType = DetermineDefectType(wavelengths[i]),
                            Severity = Math.Abs(transmissions[i] - localMean),
                            Description = $"Transmission drop of {Math.Abs(transmissions[i] - localMean):F1}% at {wavelengths[i]:F0}nm"
                        });
                        
                        // Skip nearby points to avoid duplicate detections
                        i += 5;
                    }
                }
            }

            return defects;
        }

        /// <summary>
        /// Determine likely defect type based on wavelength location.
        /// </summary>
        private string DetermineDefectType(double wavelengthNm)
        {
            return wavelengthNm switch
            {
                < 400 => "Iron impurity (Fe³⁺) or UV absorber",
                >= 400 and < 600 => "Coating defect or surface damage",
                >= 600 and < 1000 => "Inclusion or bubble",
                >= 2700 and < 2800 => "Hydroxyl (OH⁻) absorption",
                _ => "Unknown absorption feature"
            };
        }
    }
}