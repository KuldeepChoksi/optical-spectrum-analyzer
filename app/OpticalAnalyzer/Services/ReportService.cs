using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using OpticalAnalyzer.Models;

namespace OpticalAnalyzer.Services
{
    /// <summary>
    /// Service for generating QC reports in various formats.
    /// </summary>
    public interface IReportService
    {
        string GenerateTextReport(List<QualityAnalysisResult> results);
        string GenerateSampleReport(QualityAnalysisResult result);
        void ExportToCsv(List<QualityAnalysisResult> results, string filePath);
    }

    public class ReportService : IReportService
    {
        /// <summary>
        /// Generate a comprehensive text report for multiple samples.
        /// </summary>
        public string GenerateTextReport(List<QualityAnalysisResult> results)
        {
            var sb = new StringBuilder();
            
            sb.AppendLine("════════════════════════════════════════════════════════════");
            sb.AppendLine("         OPTICAL SPECTRUM ANALYZER - QC REPORT");
            sb.AppendLine("════════════════════════════════════════════════════════════");
            sb.AppendLine($"Report Generated: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
            sb.AppendLine($"Total Samples Analyzed: {results.Count}");
            sb.AppendLine();

            // Summary Statistics
            sb.AppendLine("─── QUALITY GRADE DISTRIBUTION ───");
            var gradeGroups = results.GroupBy(r => r.Grade)
                .OrderBy(g => g.Key);
            
            foreach (var grade in new[] { QualityGrade.Excellent, QualityGrade.Good, QualityGrade.Fair, QualityGrade.Poor })
            {
                var count = results.Count(r => r.Grade == grade);
                var pct = results.Count > 0 ? (count * 100.0 / results.Count) : 0;
                var bar = new string('█', (int)(pct / 5)) + new string('░', 20 - (int)(pct / 5));
                sb.AppendLine($"  {grade,-10}: {bar} {count,3} ({pct,5:F1}%)");
            }
            sb.AppendLine();

            // Pass/Fail Summary
            sb.AppendLine("─── QC PASS/FAIL SUMMARY ───");
            var passCount = results.Count(r => r.PassedQC);
            var failCount = results.Count - passCount;
            var passRate = results.Count > 0 ? (passCount * 100.0 / results.Count) : 0;
            sb.AppendLine($"  PASS: {passCount} samples ({passRate:F1}%)");
            sb.AppendLine($"  FAIL: {failCount} samples ({100 - passRate:F1}%)");
            sb.AppendLine();

            // Defect Summary
            sb.AppendLine("─── DEFECT ANALYSIS ───");
            var samplesWithDefects = results.Count(r => r.DefectCount > 0);
            var totalDefects = results.Sum(r => r.DefectCount);
            sb.AppendLine($"  Samples with defects: {samplesWithDefects}");
            sb.AppendLine($"  Total defects found: {totalDefects}");
            sb.AppendLine();

            // Material Breakdown
            sb.AppendLine("─── RESULTS BY MATERIAL ───");
            var materialGroups = results.GroupBy(r => r.MaterialType);
            sb.AppendLine($"  {"Material",-35} {"Avg T%",8} {"Pass",6} {"Fail",6}");
            sb.AppendLine($"  {new string('-', 55)}");
            
            foreach (var group in materialGroups.OrderBy(g => g.Key))
            {
                var avgT = group.Average(r => r.AvgVisibleTransmission);
                var pass = group.Count(r => r.PassedQC);
                var fail = group.Count(r => !r.PassedQC);
                var name = group.Key.Length > 33 ? group.Key[..30] + "..." : group.Key;
                sb.AppendLine($"  {name,-35} {avgT,7:F1}% {pass,6} {fail,6}");
            }
            sb.AppendLine();

            // Failed Samples Detail
            var failedSamples = results.Where(r => !r.PassedQC).ToList();
            if (failedSamples.Any())
            {
                sb.AppendLine("─── FAILED SAMPLES ───");
                foreach (var sample in failedSamples.Take(10))
                {
                    sb.AppendLine($"  • {sample.SampleId}");
                    sb.AppendLine($"    Grade: {sample.Grade}, Avg T: {sample.AvgVisibleTransmission:F1}%");
                    if (sample.Notes.Any())
                    {
                        sb.AppendLine($"    Reason: {sample.Notes.First()}");
                    }
                }
                if (failedSamples.Count > 10)
                {
                    sb.AppendLine($"  ... and {failedSamples.Count - 10} more");
                }
                sb.AppendLine();
            }

            sb.AppendLine("════════════════════════════════════════════════════════════");
            sb.AppendLine("                      END OF REPORT");
            sb.AppendLine("════════════════════════════════════════════════════════════");

            return sb.ToString();
        }

        /// <summary>
        /// Generate a detailed report for a single sample.
        /// </summary>
        public string GenerateSampleReport(QualityAnalysisResult result)
        {
            var sb = new StringBuilder();
            
            sb.AppendLine("════════════════════════════════════════════════════════════");
            sb.AppendLine("              SAMPLE QUALITY REPORT");
            sb.AppendLine("════════════════════════════════════════════════════════════");
            sb.AppendLine();
            sb.AppendLine($"Sample ID:     {result.SampleId}");
            sb.AppendLine($"Material:      {result.MaterialType}");
            sb.AppendLine($"Analysis Date: {result.AnalysisDate:yyyy-MM-dd HH:mm:ss}");
            sb.AppendLine();
            
            sb.AppendLine("─── TRANSMISSION METRICS ───");
            sb.AppendLine($"  Peak Transmission:      {result.PeakTransmission,7:F1}%");
            sb.AppendLine($"  Avg Visible (400-700):  {result.AvgVisibleTransmission,7:F1}%");
            sb.AppendLine($"  Avg Full Spectrum:      {result.AvgFullSpectrumTransmission,7:F1}%");
            sb.AppendLine($"  Bandwidth (>80%):       {result.TransmissionBandwidthNm,7:F0} nm");
            sb.AppendLine($"  Uniformity Score:       {result.UniformityScore,7:F1}%");
            sb.AppendLine();
            
            sb.AppendLine("─── DEFECT ANALYSIS ───");
            sb.AppendLine($"  Defects Detected: {result.DefectCount}");
            if (result.Defects.Any())
            {
                foreach (var defect in result.Defects)
                {
                    sb.AppendLine($"    • {defect.WavelengthNm:F0}nm: {defect.DefectType}");
                    sb.AppendLine($"      {defect.Description}");
                }
            }
            sb.AppendLine();
            
            sb.AppendLine("─── QUALITY CLASSIFICATION ───");
            sb.AppendLine($"  Quality Grade: {result.Grade}");
            sb.AppendLine($"  QC Status:     {result.PassFailText}");
            sb.AppendLine();
            
            if (result.Notes.Any())
            {
                sb.AppendLine("─── NOTES ───");
                foreach (var note in result.Notes)
                {
                    sb.AppendLine($"  • {note}");
                }
                sb.AppendLine();
            }
            
            sb.AppendLine("════════════════════════════════════════════════════════════");

            return sb.ToString();
        }

        /// <summary>
        /// Export analysis results to CSV file.
        /// </summary>
        public void ExportToCsv(List<QualityAnalysisResult> results, string filePath)
        {
            var sb = new StringBuilder();
            
            // Header
            sb.AppendLine("sample_id,material_type,peak_transmission,avg_visible_transmission," +
                         "avg_full_transmission,bandwidth_nm,uniformity_score,defect_count," +
                         "quality_grade,passed_qc,analysis_date");
            
            // Data rows
            foreach (var r in results)
            {
                sb.AppendLine($"{r.SampleId},{r.MaterialType},{r.PeakTransmission:F2}," +
                             $"{r.AvgVisibleTransmission:F2},{r.AvgFullSpectrumTransmission:F2}," +
                             $"{r.TransmissionBandwidthNm:F0},{r.UniformityScore:F2}," +
                             $"{r.DefectCount},{r.Grade},{r.PassedQC},{r.AnalysisDate:yyyy-MM-dd}");
            }
            
            File.WriteAllText(filePath, sb.ToString());
        }
    }
}