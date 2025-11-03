"""
Quality Classifier Module for Optical Spectrum Analyzer

Analyzes transmission spectra to classify material quality and detect
defects based on optical characteristics. Implements industry-standard
quality metrics for optical component manufacturing.

Quality Grades (based on ISO 10110 optical standards):
    - Excellent: >90% average transmission in visible range
    - Good: 80-90% average transmission
    - Fair: 70-80% average transmission  
    - Poor: <70% average transmission

Author: Kuldeep Choksi
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class QualityGrade(Enum):
    """Quality grade classifications for optical materials."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


@dataclass
class QualityMetrics:
    """Container for quality analysis metrics."""
    sample_id: str
    material_type: str
    peak_transmission: float
    avg_transmission_visible: float
    avg_transmission_full: float
    transmission_bandwidth_nm: float
    uniformity_score: float
    defect_count: int
    defect_locations: List[float]
    quality_grade: QualityGrade
    pass_qc: bool
    notes: List[str]


class QualityClassifier:
    """
    Analyzes optical transmission spectra for quality classification.
    
    Implements detection of:
    - Surface defects (scratches, contamination)
    - Material impurities (absorption bands)
    - Structural issues (bubbles, inclusions)
    - Coating degradation
    """
    
    # Wavelength ranges (nm)
    UV_RANGE = (200, 400)
    VISIBLE_RANGE = (400, 700)
    NIR_RANGE = (700, 1400)
    
    # Quality thresholds (average transmission in visible range)
    GRADE_THRESHOLDS = {
        QualityGrade.EXCELLENT: 90,
        QualityGrade.GOOD: 80,
        QualityGrade.FAIR: 70,
        QualityGrade.POOR: 0
    }
    
    # Defect detection parameters
    DEFECT_DROP_THRESHOLD = 0.10  # 10% sudden drop indicates defect
    DEFECT_GRADIENT_THRESHOLD = 0.5  # %/nm for sharp features
    
    def __init__(
        self, 
        visible_threshold: float = 80.0,
        bandwidth_threshold: float = 80.0
    ):
        """
        Initialize the quality classifier.
        
        Args:
            visible_threshold: Minimum average transmission (%) for pass
            bandwidth_threshold: Threshold (%) for bandwidth calculation
        """
        self.visible_threshold = visible_threshold
        self.bandwidth_threshold = bandwidth_threshold
    
    def calculate_metrics(
        self,
        wavelength_nm: np.ndarray,
        transmission_pct: np.ndarray,
        sample_id: str = "unknown",
        material_type: str = "unknown"
    ) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for a spectrum.
        
        Args:
            wavelength_nm: Wavelength array in nanometers
            transmission_pct: Transmission percentage array
            sample_id: Sample identifier
            material_type: Material type string
            
        Returns:
            QualityMetrics object with all analysis results
        """
        notes = []
        
        # Peak transmission
        peak_transmission = np.max(transmission_pct)
        peak_wavelength = wavelength_nm[np.argmax(transmission_pct)]
        
        # Average transmission in visible range
        visible_mask = (wavelength_nm >= self.VISIBLE_RANGE[0]) & \
                       (wavelength_nm <= self.VISIBLE_RANGE[1])
        if visible_mask.any():
            avg_visible = np.mean(transmission_pct[visible_mask])
        else:
            avg_visible = np.mean(transmission_pct)
            notes.append("Visible range not covered in spectrum")
        
        # Full spectrum average
        avg_full = np.mean(transmission_pct)
        
        # Transmission bandwidth (range where T > threshold)
        bandwidth = self._calculate_bandwidth(
            wavelength_nm, transmission_pct, self.bandwidth_threshold
        )
        
        # Uniformity score (inverse of coefficient of variation)
        if visible_mask.any():
            visible_trans = transmission_pct[visible_mask]
            cv = np.std(visible_trans) / np.mean(visible_trans) if np.mean(visible_trans) > 0 else 1
            uniformity = max(0, 1 - cv) * 100
        else:
            uniformity = 0
        
        # Defect detection
        defect_locations = self._detect_defects(wavelength_nm, transmission_pct)
        defect_count = len(defect_locations)
        
        if defect_count > 0:
            notes.append(f"Detected {defect_count} potential defects")
        
        # Quality grade classification
        quality_grade = self._classify_grade(avg_visible)
        
        # Pass/Fail determination
        pass_qc = (avg_visible >= self.visible_threshold) and (defect_count == 0)
        
        if not pass_qc:
            if avg_visible < self.visible_threshold:
                notes.append(f"Below transmission threshold ({avg_visible:.1f}% < {self.visible_threshold}%)")
            if defect_count > 0:
                notes.append("Failed due to detected defects")
        
        return QualityMetrics(
            sample_id=sample_id,
            material_type=material_type,
            peak_transmission=peak_transmission,
            avg_transmission_visible=avg_visible,
            avg_transmission_full=avg_full,
            transmission_bandwidth_nm=bandwidth,
            uniformity_score=uniformity,
            defect_count=defect_count,
            defect_locations=defect_locations,
            quality_grade=quality_grade,
            pass_qc=pass_qc,
            notes=notes
        )
    
    def _calculate_bandwidth(
        self,
        wavelength: np.ndarray,
        transmission: np.ndarray,
        threshold: float
    ) -> float:
        """Calculate transmission bandwidth above threshold."""
        above_threshold = transmission >= threshold
        
        if not above_threshold.any():
            return 0.0
        
        # Find contiguous regions above threshold
        indices = np.where(above_threshold)[0]
        if len(indices) == 0:
            return 0.0
        
        # Total bandwidth
        return wavelength[indices[-1]] - wavelength[indices[0]]
    
    def _detect_defects(
        self,
        wavelength: np.ndarray,
        transmission: np.ndarray
    ) -> List[float]:
        """
        Detect defects as sudden drops in transmission.
        
        Returns wavelength locations of detected defects.
        """
        defect_locations = []
        
        # Calculate first derivative (transmission gradient)
        gradient = np.gradient(transmission, wavelength)
        
        # Smooth to reduce noise
        window = min(5, len(gradient) // 10)
        if window > 1:
            kernel = np.ones(window) / window
            gradient_smooth = np.convolve(gradient, kernel, mode='same')
        else:
            gradient_smooth = gradient
        
        # Detect sharp drops (negative gradients)
        sharp_drops = np.where(gradient_smooth < -self.DEFECT_GRADIENT_THRESHOLD)[0]
        
        # Cluster nearby detections
        if len(sharp_drops) > 0:
            clusters = []
            current_cluster = [sharp_drops[0]]
            
            for i in range(1, len(sharp_drops)):
                if sharp_drops[i] - sharp_drops[i-1] < 10:  # Within 10 points
                    current_cluster.append(sharp_drops[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [sharp_drops[i]]
            clusters.append(current_cluster)
            
            # Get center of each cluster
            for cluster in clusters:
                center_idx = cluster[len(cluster)//2]
                defect_locations.append(float(wavelength[center_idx]))
        
        # Also detect localized absorption bands
        # (sudden dip and recovery)
        local_mean = np.convolve(transmission, np.ones(20)/20, mode='same')
        deviation = transmission - local_mean
        
        absorption_bands = np.where(deviation < -self.DEFECT_DROP_THRESHOLD * 100)[0]
        
        # Add unique locations
        for idx in absorption_bands:
            wl = wavelength[idx]
            # Check if not already detected
            if not any(abs(wl - loc) < 50 for loc in defect_locations):
                defect_locations.append(float(wl))
        
        return sorted(defect_locations)
    
    def _classify_grade(self, avg_transmission: float) -> QualityGrade:
        """Classify quality grade based on average transmission."""
        if avg_transmission >= self.GRADE_THRESHOLDS[QualityGrade.EXCELLENT]:
            return QualityGrade.EXCELLENT
        elif avg_transmission >= self.GRADE_THRESHOLDS[QualityGrade.GOOD]:
            return QualityGrade.GOOD
        elif avg_transmission >= self.GRADE_THRESHOLDS[QualityGrade.FAIR]:
            return QualityGrade.FAIR
        else:
            return QualityGrade.POOR
    
    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze all samples in a DataFrame.
        
        Args:
            df: DataFrame with wavelength_nm, transmission_percent, 
                sample_id, material_type columns
                
        Returns:
            DataFrame with quality metrics for each sample
        """
        results = []
        
        sample_col = 'sample_id' if 'sample_id' in df.columns else None
        
        if sample_col:
            samples = df[sample_col].unique()
        else:
            samples = [df['material_type'].iloc[0]]
        
        for sample in samples:
            if sample_col:
                sample_data = df[df[sample_col] == sample]
            else:
                sample_data = df
            
            wavelength = sample_data['wavelength_nm'].values
            transmission = sample_data['transmission_percent'].values
            material = sample_data['material_type'].iloc[0]
            
            metrics = self.calculate_metrics(
                wavelength, transmission, 
                sample_id=str(sample),
                material_type=material
            )
            
            results.append({
                'sample_id': metrics.sample_id,
                'material_type': metrics.material_type,
                'peak_transmission_pct': metrics.peak_transmission,
                'avg_visible_transmission_pct': metrics.avg_transmission_visible,
                'transmission_bandwidth_nm': metrics.transmission_bandwidth_nm,
                'uniformity_score': metrics.uniformity_score,
                'defect_count': metrics.defect_count,
                'quality_grade': metrics.quality_grade.value,
                'pass_qc': metrics.pass_qc,
                'notes': '; '.join(metrics.notes) if metrics.notes else ''
            })
        
        return pd.DataFrame(results)
    
    def generate_report(self, metrics: QualityMetrics) -> str:
        """Generate a formatted quality report for a sample."""
        report = []
        report.append("=" * 60)
        report.append("OPTICAL QUALITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nSample ID: {metrics.sample_id}")
        report.append(f"Material: {metrics.material_type}")
        report.append("\n--- TRANSMISSION METRICS ---")
        report.append(f"Peak Transmission: {metrics.peak_transmission:.1f}%")
        report.append(f"Avg Visible (400-700nm): {metrics.avg_transmission_visible:.1f}%")
        report.append(f"Avg Full Spectrum: {metrics.avg_transmission_full:.1f}%")
        report.append(f"Bandwidth (>{self.bandwidth_threshold}%): {metrics.transmission_bandwidth_nm:.0f} nm")
        report.append(f"Uniformity Score: {metrics.uniformity_score:.1f}%")
        report.append("\n--- DEFECT ANALYSIS ---")
        report.append(f"Defects Detected: {metrics.defect_count}")
        if metrics.defect_locations:
            locations = ', '.join(f"{wl:.0f}nm" for wl in metrics.defect_locations)
            report.append(f"Defect Locations: {locations}")
        report.append("\n--- QUALITY CLASSIFICATION ---")
        report.append(f"Quality Grade: {metrics.quality_grade.value}")
        report.append(f"QC Status: {'PASS ✓' if metrics.pass_qc else 'FAIL ✗'}")
        if metrics.notes:
            report.append("\nNotes:")
            for note in metrics.notes:
                report.append(f"  • {note}")
        report.append("\n" + "=" * 60)
        
        return '\n'.join(report)


def main():
    """Test the quality classifier."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import SpectroscopyDataLoader
    
    loader = SpectroscopyDataLoader()
    classifier = QualityClassifier()
    
    data_path = PROJECT_ROOT / "data" / "generated" / "optical_transmission_data.csv"
    
    if data_path.exists():
        df = loader.load_csv(data_path)
        
        # Analyze all samples
        results = classifier.analyze_dataframe(df)
        
        print("\n" + "="*60)
        print("QUALITY CLASSIFICATION SUMMARY")
        print("="*60)
        
        # Grade distribution
        print("\nQuality Grade Distribution:")
        grade_counts = results['quality_grade'].value_counts()
        for grade, count in grade_counts.items():
            pct = count / len(results) * 100
            print(f"  {grade}: {count} ({pct:.1f}%)")
        
        # Pass/Fail rate
        pass_rate = results['pass_qc'].sum() / len(results) * 100
        print(f"\nOverall Pass Rate: {pass_rate:.1f}%")
        
        # Save results
        output_path = PROJECT_ROOT / "data" / "generated" / "quality_analysis_results.csv"
        results.to_csv(output_path, index=False)
        print(f"\n✓ Results saved to {output_path}")
        
        # Show detailed report for first sample
        sample = df['sample_id'].iloc[0]
        sample_df = df[df['sample_id'] == sample]
        metrics = classifier.calculate_metrics(
            sample_df['wavelength_nm'].values,
            sample_df['transmission_percent'].values,
            sample_id=sample,
            material_type=sample_df['material_type'].iloc[0]
        )
        print("\n" + classifier.generate_report(metrics))
    else:
        print(f"Dataset not found at {data_path}")
        print("Run data_generator.py first.")


if __name__ == "__main__":
    main()