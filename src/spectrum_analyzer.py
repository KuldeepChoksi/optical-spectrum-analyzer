"""
Optical Spectrum Analyzer - Main Analysis Script

A comprehensive tool for analyzing optical transmission spectra of materials
used in optical component manufacturing. Supports quality control workflows
for materials including sapphire, fused silica, borosilicate glass, and more.

Features:
    - Load and validate spectroscopy data
    - Calculate quality metrics (transmission, bandwidth, uniformity)
    - Detect defects (scratches, impurities, inclusions)
    - Classify material quality grades
    - Generate publication-quality visualizations
    - Export statistical reports

Based on optical constants from RefractiveIndex.INFO database and
industry-standard quality criteria (ISO 10110).

Author: Kuldeep Choksi
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import SpectroscopyDataLoader
from data_generator import SpectroscopyDataGenerator
from quality_classifier import QualityClassifier, QualityGrade
from visualization import SpectrumVisualizer


class OpticalSpectrumAnalyzer:
    """
    Main orchestration class for optical spectrum analysis.
    
    Integrates data loading, quality classification, and visualization
    into a unified analysis pipeline.
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        visible_threshold: float = 80.0
    ):
        """
        Initialize the analyzer.
        
        Args:
            output_dir: Directory for output files
            visible_threshold: Minimum transmission (%) for QC pass
        """
        # Use project root for default output
        if output_dir is None:
            self.output_dir = PROJECT_ROOT / "results"
        else:
            self.output_dir = Path(output_dir)
            if not self.output_dir.is_absolute():
                self.output_dir = PROJECT_ROOT / self.output_dir
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.loader = SpectroscopyDataLoader()
        self.classifier = QualityClassifier(visible_threshold=visible_threshold)
        self.visualizer = SpectrumVisualizer(output_dir=self.output_dir / "plots")
        
        self.data: Optional[pd.DataFrame] = None
        self.quality_results: Optional[pd.DataFrame] = None
    
    def load_data(self, filepath: Path) -> pd.DataFrame:
        """Load spectroscopy data from CSV file."""
        self.data = self.loader.load_csv(filepath)
        return self.data
    
    def generate_sample_data(
        self,
        n_samples: int = 10,
        defect_probability: float = 0.25,
        seed: int = 42
    ) -> pd.DataFrame:
        """Generate synthetic spectroscopy data for testing."""
        generator = SpectroscopyDataGenerator(seed=seed)
        
        # Use project root for data output
        output_path = PROJECT_ROOT / "data" / "generated" / "optical_transmission_data.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.data = generator.generate_dataset(
            n_samples_per_material=n_samples,
            defect_probability=defect_probability,
            output_path=output_path
        )
        return self.data
    
    def analyze(self) -> pd.DataFrame:
        """
        Run complete quality analysis on loaded data.
        
        Returns:
            DataFrame with quality metrics for each sample
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() or generate_sample_data() first.")
        
        print("\n" + "="*60)
        print("OPTICAL SPECTRUM ANALYZER - QUALITY ANALYSIS")
        print("="*60)
        
        # Run classification
        self.quality_results = self.classifier.analyze_dataframe(self.data)
        
        # Save results
        results_path = self.output_dir / "quality_analysis.csv"
        self.quality_results.to_csv(results_path, index=False)
        print(f"\n✓ Quality results saved to {results_path}")
        
        return self.quality_results
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive analysis report.
        
        Returns:
            Formatted report string
        """
        if self.quality_results is None:
            raise ValueError("No analysis results. Call analyze() first.")
        
        report = []
        report.append("\n" + "="*60)
        report.append("OPTICAL SPECTRUM ANALYZER - SUMMARY REPORT")
        report.append("="*60)
        
        # Dataset overview
        report.append("\n--- DATASET OVERVIEW ---")
        report.append(f"Total samples analyzed: {len(self.quality_results)}")
        report.append(f"Material types: {self.quality_results['material_type'].nunique()}")
        
        for material in self.quality_results['material_type'].unique():
            count = len(self.quality_results[self.quality_results['material_type'] == material])
            report.append(f"  • {material}: {count} samples")
        
        # Quality distribution
        report.append("\n--- QUALITY GRADE DISTRIBUTION ---")
        grade_counts = self.quality_results['quality_grade'].value_counts()
        total = len(self.quality_results)
        
        for grade in ['Excellent', 'Good', 'Fair', 'Poor']:
            count = grade_counts.get(grade, 0)
            pct = count / total * 100
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            report.append(f"  {grade:10s}: {bar} {count:3d} ({pct:5.1f}%)")
        
        # QC pass rate
        report.append("\n--- QC PASS/FAIL SUMMARY ---")
        pass_count = self.quality_results['pass_qc'].sum()
        fail_count = len(self.quality_results) - pass_count
        pass_rate = pass_count / total * 100
        
        report.append(f"  PASS: {pass_count} samples ({pass_rate:.1f}%)")
        report.append(f"  FAIL: {fail_count} samples ({100-pass_rate:.1f}%)")
        
        # Defect summary
        report.append("\n--- DEFECT ANALYSIS ---")
        defect_samples = self.quality_results[self.quality_results['defect_count'] > 0]
        report.append(f"  Samples with defects: {len(defect_samples)} ({len(defect_samples)/total*100:.1f}%)")
        report.append(f"  Total defects detected: {self.quality_results['defect_count'].sum()}")
        report.append(f"  Avg defects per sample: {self.quality_results['defect_count'].mean():.2f}")
        
        # Transmission statistics by material
        report.append("\n--- TRANSMISSION STATISTICS BY MATERIAL ---")
        report.append(f"  {'Material':<30s} {'Avg T%':>8s} {'Min T%':>8s} {'Max T%':>8s}")
        report.append("  " + "-"*58)
        
        for material in self.quality_results['material_type'].unique():
            mat_df = self.quality_results[self.quality_results['material_type'] == material]
            avg_t = mat_df['avg_visible_transmission_pct'].mean()
            min_t = mat_df['avg_visible_transmission_pct'].min()
            max_t = mat_df['avg_visible_transmission_pct'].max()
            mat_short = material[:28] + '..' if len(material) > 30 else material
            report.append(f"  {mat_short:<30s} {avg_t:>7.1f}% {min_t:>7.1f}% {max_t:>7.1f}%")
        
        # Recommendations
        report.append("\n--- RECOMMENDATIONS ---")
        if fail_count > 0:
            report.append("  • Review failed samples for root cause analysis")
            if defect_samples['defect_count'].sum() > 0:
                report.append("  • Investigate defect sources (contamination, handling, process)")
        
        low_grade = self.quality_results[self.quality_results['quality_grade'].isin(['Fair', 'Poor'])]
        if len(low_grade) > 0:
            materials_affected = low_grade['material_type'].unique()
            report.append(f"  • Materials requiring attention: {', '.join(m[:15] for m in materials_affected)}")
        
        if pass_rate >= 90:
            report.append("  ✓ Overall quality is excellent - maintain current processes")
        elif pass_rate >= 75:
            report.append("  • Quality is acceptable but has room for improvement")
        else:
            report.append("  ⚠ Quality requires immediate attention")
        
        report.append("\n" + "="*60)
        report.append("END OF REPORT")
        report.append("="*60 + "\n")
        
        report_text = '\n'.join(report)
        
        # Save report
        report_path = self.output_dir / "analysis_report.txt"
        with open(report_path, 'w') as f:
            f.write(report_text)
        print(f"✓ Report saved to {report_path}")
        
        return report_text
    
    def generate_visualizations(self) -> None:
        """Generate all standard visualizations."""
        if self.data is None or self.quality_results is None:
            raise ValueError("Run analyze() before generating visualizations.")
        
        print("\nGenerating visualizations...")
        
        # Material comparison
        self.visualizer.plot_material_comparison(
            self.data,
            title="Optical Material Transmission Comparison",
            save_path="material_comparison.png"
        )
        
        # Quality distribution
        self.visualizer.plot_quality_distribution(
            self.quality_results,
            save_path="quality_distribution.png"
        )
        
        # Individual sample spectra (first 5 with defects)
        defect_samples = self.quality_results[self.quality_results['defect_count'] > 0].head(5)
        for _, row in defect_samples.iterrows():
            sample_id = row['sample_id']
            sample_df = self.data[self.data['sample_id'] == sample_id]
            
            metrics = self.classifier.calculate_metrics(
                sample_df['wavelength_nm'].values,
                sample_df['transmission_percent'].values,
                sample_id=sample_id,
                material_type=row['material_type']
            )
            
            self.visualizer.plot_spectrum(
                sample_df['wavelength_nm'].values,
                sample_df['transmission_percent'].values,
                title=f"Defect Analysis: {sample_id}",
                material=row['material_type'],
                defect_locations=metrics.defect_locations,
                save_path=f"defect_{sample_id}.png"
            )
        
        print(f"✓ Visualizations saved to {self.visualizer.output_dir}/")


def main():
    """Main entry point for the Optical Spectrum Analyzer."""
    parser = argparse.ArgumentParser(
        description='Optical Spectrum Analyzer - Material Quality Control Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze existing data file
  python spectrum_analyzer.py --input data/measurements.csv
  
  # Generate sample data and analyze
  python spectrum_analyzer.py --generate --samples 15
  
  # Full analysis with visualizations
  python spectrum_analyzer.py --input data/data.csv --visualize --report
        """
    )
    
    parser.add_argument('--input', '-i', type=Path, 
                       help='Input CSV file with spectroscopy data')
    parser.add_argument('--output', '-o', type=Path, default=Path('results'),
                       help='Output directory (default: results)')
    parser.add_argument('--generate', '-g', action='store_true',
                       help='Generate synthetic sample data')
    parser.add_argument('--samples', '-n', type=int, default=10,
                       help='Samples per material for generation (default: 10)')
    parser.add_argument('--threshold', '-t', type=float, default=80.0,
                       help='QC pass threshold (default: 80%%)')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Generate visualization plots')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Generate analysis report')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = OpticalSpectrumAnalyzer(
        output_dir=args.output,
        visible_threshold=args.threshold
    )
    
    # Load or generate data
    if args.generate:
        print(f"Generating synthetic data ({args.samples} samples per material)...")
        analyzer.generate_sample_data(n_samples=args.samples)
    elif args.input:
        if not args.input.exists():
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        analyzer.load_data(args.input)
    else:
        # Default: generate sample data
        print("No input specified. Generating sample data...")
        analyzer.generate_sample_data()
    
    # Run analysis
    analyzer.analyze()
    
    # Generate report
    if args.report or not args.input:
        report = analyzer.generate_report()
        print(report)
    
    # Generate visualizations
    if args.visualize or not args.input:
        analyzer.generate_visualizations()
    
    print("\n✓ Analysis complete!")
    print(f"  Results saved to: {args.output}/")


if __name__ == "__main__":
    main()