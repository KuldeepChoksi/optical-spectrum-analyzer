using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using CsvHelper;
using CsvHelper.Configuration;
using OpticalAnalyzer.Models;

namespace OpticalAnalyzer.Services
{
    /// <summary>
    /// Service for loading and managing spectrum data.
    /// </summary>
    public interface ISpectrumDataService
    {
        Task<List<SpectrumData>> LoadFromCsvAsync(string filePath);
        List<string> GetUniqueSampleIds(List<SpectrumData> spectra);
        List<string> GetUniqueMaterials(List<SpectrumData> spectra);
        SpectrumData? GetSampleById(List<SpectrumData> spectra, string sampleId);
    }

    public class SpectrumDataService : ISpectrumDataService
    {
        /// <summary>
        /// Load spectrum data from a CSV file.
        /// Expected columns: wavelength_nm, transmission_percent, material_type, sample_id
        /// </summary>
        public async Task<List<SpectrumData>> LoadFromCsvAsync(string filePath)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException($"CSV file not found: {filePath}");

            var spectraDict = new Dictionary<string, SpectrumData>();

            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                HasHeaderRecord = true,
                MissingFieldFound = null,
                HeaderValidated = null
            };

            await Task.Run(() =>
            {
                using var reader = new StreamReader(filePath);
                using var csv = new CsvReader(reader, config);
                
                var records = csv.GetRecords<CsvSpectrumRow>();

                foreach (var row in records)
                {
                    var sampleId = string.IsNullOrEmpty(row.sample_id) 
                        ? $"{row.material_type}_default" 
                        : row.sample_id;

                    if (!spectraDict.ContainsKey(sampleId))
                    {
                        spectraDict[sampleId] = new SpectrumData
                        {
                            SampleId = sampleId,
                            MaterialType = row.material_type,
                            ThicknessMm = row.thickness_mm > 0 ? row.thickness_mm : 2.0,
                            DataPoints = new List<SpectrumDataPoint>()
                        };
                    }

                    spectraDict[sampleId].DataPoints.Add(new SpectrumDataPoint
                    {
                        WavelengthNm = row.wavelength_nm,
                        TransmissionPercent = row.transmission_percent
                    });
                }
            });

            // Sort data points by wavelength for each spectrum
            foreach (var spectrum in spectraDict.Values)
            {
                spectrum.DataPoints = spectrum.DataPoints
                    .OrderBy(p => p.WavelengthNm)
                    .ToList();
            }

            return spectraDict.Values.ToList();
        }

        /// <summary>
        /// Get list of unique sample IDs from loaded spectra.
        /// </summary>
        public List<string> GetUniqueSampleIds(List<SpectrumData> spectra)
        {
            return spectra.Select(s => s.SampleId).Distinct().OrderBy(s => s).ToList();
        }

        /// <summary>
        /// Get list of unique material types from loaded spectra.
        /// </summary>
        public List<string> GetUniqueMaterials(List<SpectrumData> spectra)
        {
            return spectra.Select(s => s.MaterialType).Distinct().OrderBy(s => s).ToList();
        }

        /// <summary>
        /// Get a specific sample by ID.
        /// </summary>
        public SpectrumData? GetSampleById(List<SpectrumData> spectra, string sampleId)
        {
            return spectra.FirstOrDefault(s => s.SampleId == sampleId);
        }
    }
}