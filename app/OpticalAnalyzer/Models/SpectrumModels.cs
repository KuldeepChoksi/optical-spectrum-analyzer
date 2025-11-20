using System;
using System.Collections.Generic;

namespace OpticalAnalyzer.Models
{
    /// <summary>
    /// Represents a single data point in a transmission spectrum.
    /// </summary>
    public class SpectrumDataPoint
    {
        public double WavelengthNm { get; set; }
        public double TransmissionPercent { get; set; }
    }

    /// <summary>
    /// Represents a complete transmission spectrum for a sample.
    /// </summary>
    public class SpectrumData
    {
        public string SampleId { get; set; } = string.Empty;
        public string MaterialType { get; set; } = string.Empty;
        public double ThicknessMm { get; set; }
        public DateTime MeasurementDate { get; set; } = DateTime.Now;
        public List<SpectrumDataPoint> DataPoints { get; set; } = new();

        public double MinWavelength => DataPoints.Count > 0 
            ? DataPoints.Min(p => p.WavelengthNm) : 0;
        public double MaxWavelength => DataPoints.Count > 0 
            ? DataPoints.Max(p => p.WavelengthNm) : 0;
        public double PeakTransmission => DataPoints.Count > 0 
            ? DataPoints.Max(p => p.TransmissionPercent) : 0;
    }

    /// <summary>
    /// Quality grade classification based on ISO 10110 standards.
    /// </summary>
    public enum QualityGrade
    {
        Excellent,  // >= 90% avg visible transmission
        Good,       // 80-90%
        Fair,       // 70-80%
        Poor        // < 70%
    }

    /// <summary>
    /// Detected defect in a spectrum.
    /// </summary>
    public class DefectInfo
    {
        public double WavelengthNm { get; set; }
        public string DefectType { get; set; } = string.Empty;
        public double Severity { get; set; }
        public string Description { get; set; } = string.Empty;
    }

    /// <summary>
    /// Complete quality analysis results for a sample.
    /// </summary>
    public class QualityAnalysisResult
    {
        public string SampleId { get; set; } = string.Empty;
        public string MaterialType { get; set; } = string.Empty;
        
        // Transmission metrics
        public double PeakTransmission { get; set; }
        public double AvgVisibleTransmission { get; set; }
        public double AvgFullSpectrumTransmission { get; set; }
        public double TransmissionBandwidthNm { get; set; }
        
        // Quality assessment
        public double UniformityScore { get; set; }
        public QualityGrade Grade { get; set; }
        public bool PassedQC { get; set; }
        
        // Defect analysis
        public int DefectCount { get; set; }
        public List<DefectInfo> Defects { get; set; } = new();
        
        // Notes
        public List<string> Notes { get; set; } = new();
        public DateTime AnalysisDate { get; set; } = DateTime.Now;

        public string GradeColor => Grade switch
        {
            QualityGrade.Excellent => "#22C55E",
            QualityGrade.Good => "#3B82F6",
            QualityGrade.Fair => "#F59E0B",
            QualityGrade.Poor => "#EF4444",
            _ => "#64748B"
        };

        public string PassFailText => PassedQC ? "PASS ✓" : "FAIL ✗";
        public string PassFailColor => PassedQC ? "#22C55E" : "#EF4444";
    }

    /// <summary>
    /// Material information from the database.
    /// </summary>
    public class MaterialInfo
    {
        public string Key { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Formula { get; set; } = string.Empty;
        public double UvCutoffNm { get; set; }
        public double IrCutoffNm { get; set; }
        public double PeakTransmission { get; set; }
        public string Reference { get; set; } = string.Empty;
    }

    /// <summary>
    /// CSV import row mapping.
    /// </summary>
    public class CsvSpectrumRow
    {
        public double wavelength_nm { get; set; }
        public double transmission_percent { get; set; }
        public string material_type { get; set; } = string.Empty;
        public string sample_id { get; set; } = string.Empty;
        public double thickness_mm { get; set; }
        public bool has_defects { get; set; }
    }
}