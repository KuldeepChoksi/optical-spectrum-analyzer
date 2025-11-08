"""
Visualization Module for Optical Spectrum Analyzer

Generates publication-quality plots for optical transmission analysis:
- Individual spectrum plots
- Material comparison charts
- Quality distribution visualizations
- Defect highlighting

Author: Kuldeep Choksi
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Set publication-quality defaults
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Color palette for materials
MATERIAL_COLORS = {
    'sapphire': '#1f77b4',
    'fused_silica': '#ff7f0e', 
    'borosilicate_bk7': '#2ca02c',
    'soda_lime': '#d62728',
    'quartz_crystalline': '#9467bd',
    'calcium_fluoride': '#8c564b',
    'zinc_selenide': '#e377c2',
    'pmma': '#7f7f7f'
}

# Spectral region colors
SPECTRAL_REGIONS = {
    'UV': {'range': (200, 400), 'color': '#9b59b6', 'alpha': 0.15},
    'Visible': {'range': (400, 700), 'color': '#f1c40f', 'alpha': 0.15},
    'NIR': {'range': (700, 1400), 'color': '#e74c3c', 'alpha': 0.15},
    'MIR': {'range': (1400, 3000), 'color': '#c0392b', 'alpha': 0.10}
}


class SpectrumVisualizer:
    """Creates visualizations for optical transmission spectra."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save plots (default: results/plots)
        """
        if output_dir is None:
            self.output_dir = PROJECT_ROOT / "results" / "plots"
        else:
            self.output_dir = Path(output_dir)
            if not self.output_dir.is_absolute():
                self.output_dir = PROJECT_ROOT / self.output_dir
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_spectrum(
        self,
        wavelength: np.ndarray,
        transmission: np.ndarray,
        title: str = "Optical Transmission Spectrum",
        material: Optional[str] = None,
        show_regions: bool = True,
        defect_locations: Optional[List[float]] = None,
        save_path: Optional[str] = None,
        ax: Optional[plt.Axes] = None
    ) -> plt.Figure:
        """
        Plot a single transmission spectrum.
        
        Args:
            wavelength: Wavelength array in nm
            transmission: Transmission percentage array
            title: Plot title
            material: Material name for color coding
            show_regions: Whether to show UV/Vis/NIR regions
            defect_locations: List of wavelengths where defects were detected
            save_path: Path to save the figure
            ax: Existing axes to plot on
            
        Returns:
            matplotlib Figure object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        else:
            fig = ax.get_figure()
        
        # Show spectral regions
        if show_regions:
            for region_name, region_info in SPECTRAL_REGIONS.items():
                wl_min, wl_max = region_info['range']
                if wavelength.min() <= wl_max and wavelength.max() >= wl_min:
                    ax.axvspan(
                        max(wl_min, wavelength.min()),
                        min(wl_max, wavelength.max()),
                        color=region_info['color'],
                        alpha=region_info['alpha'],
                        label=region_name
                    )
        
        # Get color for material
        color = '#1f77b4'
        if material:
            for key, mat_color in MATERIAL_COLORS.items():
                if key in material.lower():
                    color = mat_color
                    break
        
        # Plot spectrum
        ax.plot(wavelength, transmission, color=color, linewidth=1.5, label=material or 'Spectrum')
        
        # Mark defect locations
        if defect_locations:
            for wl in defect_locations:
                if wavelength.min() <= wl <= wavelength.max():
                    idx = np.argmin(np.abs(wavelength - wl))
                    ax.plot(wl, transmission[idx], 'rv', markersize=10, 
                           label='Defect' if wl == defect_locations[0] else '')
                    ax.annotate(
                        f'{wl:.0f}nm',
                        xy=(wl, transmission[idx]),
                        xytext=(5, 10),
                        textcoords='offset points',
                        fontsize=9,
                        color='red'
                    )
        
        # Formatting
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Transmission (%)')
        ax.set_title(title)
        ax.set_ylim(0, 105)
        ax.set_xlim(wavelength.min(), wavelength.max())
        
        # Add reference lines
        ax.axhline(y=90, color='green', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.axhline(y=80, color='orange', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
        
        # Add quality grade annotations
        ax.text(wavelength.max() + 20, 92, 'Excellent', fontsize=8, color='green', va='center')
        ax.text(wavelength.max() + 20, 82, 'Good', fontsize=8, color='orange', va='center')
        ax.text(wavelength.max() + 20, 72, 'Fair', fontsize=8, color='red', va='center')
        
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(self.output_dir / save_path)
            logger.info(f"Saved plot to {self.output_dir / save_path}")
        
        return fig
    
    def plot_material_comparison(
        self,
        df: pd.DataFrame,
        materials: Optional[List[str]] = None,
        title: str = "Material Transmission Comparison",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Compare transmission spectra of different materials.
        
        Args:
            df: DataFrame with wavelength_nm, transmission_percent, material_type
            materials: List of material types to include (None = all)
            title: Plot title
            save_path: Path to save the figure
            
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        if materials is None:
            materials = df['material_type'].unique()
        
        # Show spectral regions
        for region_name, region_info in SPECTRAL_REGIONS.items():
            wl_min, wl_max = region_info['range']
            ax.axvspan(wl_min, wl_max, color=region_info['color'], 
                      alpha=region_info['alpha'], label=region_name)
        
        # Plot average spectrum for each material
        for material in materials:
            mat_df = df[df['material_type'] == material]
            
            # Group by wavelength and calculate mean
            avg_spectrum = mat_df.groupby('wavelength_nm')['transmission_percent'].mean()
            
            # Get color
            color = '#7f7f7f'
            for key, mat_color in MATERIAL_COLORS.items():
                if key in material.lower():
                    color = mat_color
                    break
            
            ax.plot(avg_spectrum.index, avg_spectrum.values, 
                   color=color, linewidth=2, label=material)
        
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Transmission (%)')
        ax.set_title(title)
        ax.set_ylim(0, 105)
        ax.legend(loc='lower right', ncol=2)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(self.output_dir / save_path)
            logger.info(f"Saved comparison plot to {self.output_dir / save_path}")
        
        return fig
    
    def plot_quality_distribution(
        self,
        quality_df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a quality grade distribution visualization.
        
        Args:
            quality_df: DataFrame from QualityClassifier.analyze_dataframe()
            save_path: Path to save the figure
            
        Returns:
            matplotlib Figure object
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # 1. Quality grade pie chart
        ax1 = axes[0]
        grade_counts = quality_df['quality_grade'].value_counts()
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
        grade_order = ['Excellent', 'Good', 'Fair', 'Poor']
        ordered_counts = [grade_counts.get(g, 0) for g in grade_order]
        
        wedges, texts, autotexts = ax1.pie(
            ordered_counts, 
            labels=grade_order,
            colors=colors[:len(grade_order)],
            autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
            startangle=90
        )
        ax1.set_title('Quality Grade Distribution')
        
        # 2. Transmission histogram by material
        ax2 = axes[1]
        materials = quality_df['material_type'].unique()
        x = np.arange(len(materials))
        width = 0.35
        
        pass_counts = []
        fail_counts = []
        for mat in materials:
            mat_df = quality_df[quality_df['material_type'] == mat]
            pass_counts.append(mat_df['pass_qc'].sum())
            fail_counts.append((~mat_df['pass_qc']).sum())
        
        ax2.bar(x - width/2, pass_counts, width, label='Pass', color='#2ecc71')
        ax2.bar(x + width/2, fail_counts, width, label='Fail', color='#e74c3c')
        ax2.set_xlabel('Material Type')
        ax2.set_ylabel('Sample Count')
        ax2.set_title('QC Results by Material')
        ax2.set_xticks(x)
        ax2.set_xticklabels([m[:15] + '...' if len(m) > 15 else m for m in materials], 
                           rotation=45, ha='right')
        ax2.legend()
        
        # 3. Transmission vs Defect scatter
        ax3 = axes[2]
        colors = ['#2ecc71' if p else '#e74c3c' for p in quality_df['pass_qc']]
        ax3.scatter(
            quality_df['avg_visible_transmission_pct'],
            quality_df['defect_count'],
            c=colors, alpha=0.6, s=50
        )
        ax3.axvline(x=80, color='orange', linestyle='--', alpha=0.7, label='QC Threshold')
        ax3.set_xlabel('Average Visible Transmission (%)')
        ax3.set_ylabel('Defect Count')
        ax3.set_title('Transmission vs Defects')
        
        # Add legend
        pass_patch = mpatches.Patch(color='#2ecc71', label='Pass')
        fail_patch = mpatches.Patch(color='#e74c3c', label='Fail')
        ax3.legend(handles=[pass_patch, fail_patch, ax3.get_lines()[0]])
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(self.output_dir / save_path)
            logger.info(f"Saved quality distribution to {self.output_dir / save_path}")
        
        return fig
    
    def plot_defect_analysis(
        self,
        wavelength: np.ndarray,
        transmission: np.ndarray,
        defect_locations: List[float],
        title: str = "Defect Analysis",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create detailed defect analysis visualization.
        
        Args:
            wavelength: Wavelength array in nm
            transmission: Transmission percentage array
            defect_locations: List of defect wavelength locations
            title: Plot title
            save_path: Path to save the figure
            
        Returns:
            matplotlib Figure object
        """
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
        
        # Top: Full spectrum with defect markers
        ax1 = axes[0]
        ax1.plot(wavelength, transmission, 'b-', linewidth=1, label='Spectrum')
        ax1.fill_between(wavelength, transmission, alpha=0.3)
        
        for i, wl in enumerate(defect_locations):
            if wavelength.min() <= wl <= wavelength.max():
                idx = np.argmin(np.abs(wavelength - wl))
                ax1.axvline(wl, color='red', linestyle='--', alpha=0.5)
                ax1.plot(wl, transmission[idx], 'rv', markersize=12)
                ax1.annotate(
                    f'Defect {i+1}\n{wl:.0f}nm',
                    xy=(wl, transmission[idx]),
                    xytext=(10, -20),
                    textcoords='offset points',
                    fontsize=9,
                    color='red',
                    arrowprops=dict(arrowstyle='->', color='red', alpha=0.7)
                )
        
        ax1.set_ylabel('Transmission (%)')
        ax1.set_title(title)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Bottom: Gradient (derivative) showing defect signatures
        ax2 = axes[1]
        gradient = np.gradient(transmission, wavelength)
        ax2.plot(wavelength, gradient, 'g-', linewidth=1, label='dT/dλ')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.axhline(y=-0.5, color='red', linestyle='--', alpha=0.5, 
                   label='Defect threshold')
        ax2.axhline(y=0.5, color='red', linestyle='--', alpha=0.5)
        
        for wl in defect_locations:
            if wavelength.min() <= wl <= wavelength.max():
                ax2.axvline(wl, color='red', linestyle='--', alpha=0.5)
        
        ax2.set_xlabel('Wavelength (nm)')
        ax2.set_ylabel('Gradient (%/nm)')
        ax2.set_title('Transmission Gradient (Defect Detection)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(self.output_dir / save_path)
            logger.info(f"Saved defect analysis to {self.output_dir / save_path}")
        
        return fig


def main():
    """Generate example visualizations."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import SpectroscopyDataLoader
    from quality_classifier import QualityClassifier
    
    loader = SpectroscopyDataLoader()
    classifier = QualityClassifier()
    visualizer = SpectrumVisualizer()
    
    data_path = PROJECT_ROOT / "data" / "generated" / "optical_transmission_data.csv"
    
    if data_path.exists():
        df = loader.load_csv(data_path)
        quality_df = classifier.analyze_dataframe(df)
        
        print("\nGenerating visualizations...")
        
        # Material comparison
        visualizer.plot_material_comparison(
            df, 
            title="Optical Material Transmission Comparison",
            save_path="material_comparison.png"
        )
        
        # Quality distribution
        visualizer.plot_quality_distribution(
            quality_df,
            save_path="quality_distribution.png"
        )
        
        # Individual spectrum (first sample)
        sample = df['sample_id'].iloc[0]
        sample_df = df[df['sample_id'] == sample]
        metrics = classifier.calculate_metrics(
            sample_df['wavelength_nm'].values,
            sample_df['transmission_percent'].values,
            sample_id=sample,
            material_type=sample_df['material_type'].iloc[0]
        )
        
        visualizer.plot_spectrum(
            sample_df['wavelength_nm'].values,
            sample_df['transmission_percent'].values,
            title=f"Spectrum: {sample}",
            material=metrics.material_type,
            defect_locations=metrics.defect_locations,
            save_path=f"spectrum_{sample}.png"
        )
        
        print(f"\n✓ Plots saved to {visualizer.output_dir}/")
    else:
        print(f"Dataset not found at {data_path}")
        print("Run data_generator.py first.")


if __name__ == "__main__":
    main()