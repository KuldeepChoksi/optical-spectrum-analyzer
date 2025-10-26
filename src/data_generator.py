"""
Synthetic Spectroscopy Data Generator for Optical Spectrum Analyzer

Generates realistic optical transmission data based on Beer-Lambert Law:
    T = exp(-α * d)
    
Where:
    T = Transmission (0-1)
    α = Absorption coefficient (wavelength-dependent, cm^-1)
    d = Material thickness (cm)

Material optical properties sourced from:
    - RefractiveIndex.INFO database (Polyanskiy, 2024) - CC0 Public Domain
    - Malitson, I.H. (1965) J. Opt. Soc. Am. 55, 1205-1208 (Fused Silica)
    - Malitson, I.H. & Dodge, M.J. (1972) J. Opt. Soc. Am. 62, 1405 (Sapphire)
    - Crystran Ltd optical materials handbook (Sapphire, BK7)
    - SCHOTT AG optical glass datasheets (N-BK7)

Author: Kuldeep Choksi
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


@dataclass
class MaterialProperties:
    """
    Optical properties for a material based on published data.
    
    Refractive index data is used to calculate Fresnel reflection losses.
    Transmission ranges and absorption characteristics are from manufacturer specs.
    """
    name: str
    formula: str                      # Chemical formula
    transmission_range_nm: Tuple[float, float]  # (UV cutoff, IR cutoff)
    n_visible: float                  # Refractive index at 550nm (visible)
    peak_transmission: float          # Maximum internal transmission (0-1)
    absorption_coef_base: float       # Base absorption coefficient at 550nm (cm^-1)
    sellmeier_coeffs: Optional[Dict] = None  # For precise n(λ) calculation
    description: str = ""
    reference: str = ""


# Material database with REAL optical constants from published sources
MATERIAL_DATABASE: Dict[str, MaterialProperties] = {
    'sapphire': MaterialProperties(
        name='Sapphire (α-Al₂O₃)',
        formula='Al2O3',
        transmission_range_nm=(170, 5500),
        n_visible=1.7680,  # At 590nm, from Crystran handbook
        peak_transmission=0.93,
        absorption_coef_base=0.003,  # Very low, 0.3×10⁻³ cm⁻¹ at 2.4μm
        sellmeier_coeffs={
            'B1': 1.4313493, 'B2': 0.65054713, 'B3': 5.3414021,
            'C1': 0.0052799261, 'C2': 0.0142382647, 'C3': 325.01783
        },
        description='Single crystal corundum, excellent UV-IR transmission',
        reference='Malitson & Dodge (1972), Crystran Ltd'
    ),
    'fused_silica': MaterialProperties(
        name='Fused Silica (SiO₂)',
        formula='SiO2',
        transmission_range_nm=(180, 3500),
        n_visible=1.4585,  # At 589nm (sodium D-line)
        peak_transmission=0.935,
        absorption_coef_base=0.001,
        sellmeier_coeffs={
            'B1': 0.6961663, 'B2': 0.4079426, 'B3': 0.8974794,
            'C1': 0.0046791, 'C2': 0.0135121, 'C3': 97.9340
        },
        description='Amorphous SiO₂, excellent UV transmission to 180nm',
        reference='Malitson (1965) J. Opt. Soc. Am. 55, 1205-1208'
    ),
    'borosilicate_bk7': MaterialProperties(
        name='Borosilicate Crown Glass (N-BK7)',
        formula='SiO2-B2O3',
        transmission_range_nm=(350, 2500),
        n_visible=1.5168,  # At 587.6nm (Helium d-line)
        peak_transmission=0.92,
        absorption_coef_base=0.005,
        sellmeier_coeffs={
            'B1': 1.03961212, 'B2': 0.231792344, 'B3': 1.01046945,
            'C1': 0.00600069867, 'C2': 0.0200179144, 'C3': 103.560653
        },
        description='Standard optical glass, visible/NIR applications',
        reference='SCHOTT AG N-BK7 datasheet'
    ),
    'soda_lime': MaterialProperties(
        name='Soda-Lime Glass',
        formula='SiO2-Na2O-CaO',
        transmission_range_nm=(320, 2200),
        n_visible=1.5230,
        peak_transmission=0.89,
        absorption_coef_base=0.015,
        description='Standard window glass, limited UV transmission',
        reference='Generic float glass specifications'
    ),
    'quartz_crystalline': MaterialProperties(
        name='Crystalline Quartz',
        formula='SiO2',
        transmission_range_nm=(180, 4000),
        n_visible=1.5443,  # Ordinary ray at 589nm
        peak_transmission=0.93,
        absorption_coef_base=0.002,
        description='Natural crystalline SiO₂, birefringent',
        reference='RefractiveIndex.INFO database'
    ),
    'calcium_fluoride': MaterialProperties(
        name='Calcium Fluoride (CaF₂)',
        formula='CaF2',
        transmission_range_nm=(130, 10000),
        n_visible=1.4338,
        peak_transmission=0.95,
        absorption_coef_base=0.0005,
        sellmeier_coeffs={
            'B1': 0.5675888, 'B2': 0.4710914, 'B3': 3.8484723,
            'C1': 0.00252643, 'C2': 0.01007833, 'C3': 1200.556
        },
        description='Excellent UV-IR transmission, low dispersion',
        reference='RefractiveIndex.INFO database'
    ),
    'zinc_selenide': MaterialProperties(
        name='Zinc Selenide (ZnSe)',
        formula='ZnSe',
        transmission_range_nm=(550, 18000),
        n_visible=2.67,  # At 630nm
        peak_transmission=0.71,
        absorption_coef_base=0.0005,
        description='IR material for CO₂ laser optics, yellow color',
        reference='RefractiveIndex.INFO database'
    ),
    'pmma': MaterialProperties(
        name='PMMA (Acrylic)',
        formula='C5O2H8',
        transmission_range_nm=(380, 2200),
        n_visible=1.4914,
        peak_transmission=0.92,
        absorption_coef_base=0.02,
        description='Optical grade polymer, visible range only',
        reference='Generic PMMA optical specifications'
    )
}


@dataclass
class DefectProfile:
    """
    Defines optical signatures of common defects in optical materials.
    Based on real-world quality control observations.
    """
    name: str
    defect_type: str  # 'broadband', 'absorption_band', 'scatter'
    wavelength_center_nm: Optional[float]  # Center for absorption bands
    bandwidth_nm: Optional[float]          # Width of absorption feature
    transmission_loss: float               # Fractional loss (0-1)
    description: str


DEFECT_PROFILES: Dict[str, DefectProfile] = {
    'surface_scratch': DefectProfile(
        name='Surface Scratch',
        defect_type='broadband',
        wavelength_center_nm=None,
        bandwidth_nm=None,
        transmission_loss=0.12,
        description='Surface damage causing wavelength-independent scattering'
    ),
    'iron_impurity': DefectProfile(
        name='Iron Impurity (Fe³⁺)',
        defect_type='absorption_band',
        wavelength_center_nm=380,
        bandwidth_nm=80,
        transmission_loss=0.20,
        description='Common glass contaminant causing UV/blue absorption'
    ),
    'hydroxyl_absorption': DefectProfile(
        name='OH⁻ Absorption',
        defect_type='absorption_band',
        wavelength_center_nm=2730,
        bandwidth_nm=150,
        transmission_loss=0.35,
        description='Water/hydroxyl absorption band in silica glasses'
    ),
    'bubble_inclusion': DefectProfile(
        name='Gas Bubble/Inclusion',
        defect_type='scatter',
        wavelength_center_nm=None,
        bandwidth_nm=None,
        transmission_loss=0.08,
        description='Internal void causing Rayleigh-type scattering'
    ),
    'thermal_stress': DefectProfile(
        name='Residual Thermal Stress',
        defect_type='broadband',
        wavelength_center_nm=None,
        bandwidth_nm=None,
        transmission_loss=0.10,
        description='Birefringence from improper annealing'
    ),
    'coating_degradation': DefectProfile(
        name='AR Coating Defect',
        defect_type='absorption_band',
        wavelength_center_nm=550,
        bandwidth_nm=120,
        transmission_loss=0.15,
        description='Anti-reflective coating damage or delamination'
    )
}


class SpectroscopyDataGenerator:
    """
    Generates synthetic optical transmission spectra based on real material properties.
    
    Uses Beer-Lambert law with wavelength-dependent absorption and Fresnel
    reflection losses calculated from refractive index data.
    """
    
    def __init__(self, seed: Optional[int] = 42):
        self.rng = np.random.default_rng(seed)
        self.materials = MATERIAL_DATABASE
        self.defects = DEFECT_PROFILES
    
    def _sellmeier_n(self, wavelength_um: np.ndarray, coeffs: Dict) -> np.ndarray:
        """Calculate refractive index using Sellmeier equation."""
        λ2 = wavelength_um ** 2
        n2 = 1 + (coeffs['B1'] * λ2 / (λ2 - coeffs['C1']) +
                  coeffs['B2'] * λ2 / (λ2 - coeffs['C2']) +
                  coeffs['B3'] * λ2 / (λ2 - coeffs['C3']))
        return np.sqrt(np.maximum(n2, 1.0))
    
    def _fresnel_loss(self, n: np.ndarray) -> np.ndarray:
        """Calculate Fresnel reflection loss at normal incidence (2 surfaces)."""
        R_single = ((n - 1) / (n + 1)) ** 2
        return (1 - R_single) ** 2  # Two surfaces
    
    def _absorption_coefficient(
        self, 
        wavelength_nm: np.ndarray, 
        material: MaterialProperties
    ) -> np.ndarray:
        """
        Calculate wavelength-dependent absorption coefficient.
        
        Models UV absorption edge (Urbach tail) and IR multiphonon absorption.
        """
        uv_cutoff, ir_cutoff = material.transmission_range_nm
        α_base = material.absorption_coef_base
        
        # Start with base absorption
        α = np.ones_like(wavelength_nm, dtype=float) * α_base
        
        # UV absorption edge (Urbach tail model)
        uv_region = wavelength_nm < uv_cutoff + 50
        α[uv_region] += np.exp((uv_cutoff - wavelength_nm[uv_region]) / 20) * 0.5
        
        # IR absorption edge (multiphonon)
        ir_region = wavelength_nm > ir_cutoff - 200
        α[ir_region] += np.exp((wavelength_nm[ir_region] - ir_cutoff) / 100) * 0.3
        
        return α
    
    def _apply_defect(
        self,
        transmission: np.ndarray,
        wavelength_nm: np.ndarray,
        defect: DefectProfile
    ) -> np.ndarray:
        """Apply defect signature to transmission spectrum."""
        if defect.defect_type == 'broadband':
            return transmission * (1 - defect.transmission_loss)
        
        elif defect.defect_type == 'absorption_band':
            gaussian = np.exp(-0.5 * ((wavelength_nm - defect.wavelength_center_nm) 
                                       / (defect.bandwidth_nm / 2.355)) ** 2)
            return transmission * (1 - defect.transmission_loss * gaussian)
        
        elif defect.defect_type == 'scatter':
            # Rayleigh-type scattering (∝ λ⁻⁴)
            λ_ref = 550
            scatter_loss = defect.transmission_loss * (λ_ref / wavelength_nm) ** 4
            scatter_loss = np.clip(scatter_loss, 0, defect.transmission_loss * 2)
            return transmission * (1 - scatter_loss)
        
        return transmission
    
    def generate_spectrum(
        self,
        material_key: str,
        wavelength_nm: Optional[np.ndarray] = None,
        thickness_mm: float = 2.0,
        defects: Optional[List[str]] = None,
        noise_level: float = 0.005
    ) -> pd.DataFrame:
        """
        Generate a transmission spectrum for a material.
        
        Args:
            material_key: Key from MATERIAL_DATABASE
            wavelength_nm: Wavelength array (default: 200-2500nm)
            thickness_mm: Sample thickness in mm
            defects: List of defect keys to apply
            noise_level: Standard deviation of measurement noise
            
        Returns:
            DataFrame with wavelength_nm, transmission_percent, material_type
        """
        if material_key not in self.materials:
            raise ValueError(f"Unknown material: {material_key}")
        
        material = self.materials[material_key]
        
        if wavelength_nm is None:
            wavelength_nm = np.arange(200, 2501, 2)
        
        thickness_cm = thickness_mm / 10
        wavelength_um = wavelength_nm / 1000
        
        # Calculate refractive index
        if material.sellmeier_coeffs:
            n = self._sellmeier_n(wavelength_um, material.sellmeier_coeffs)
        else:
            n = np.full_like(wavelength_nm, material.n_visible, dtype=float)
        
        # Beer-Lambert transmission
        α = self._absorption_coefficient(wavelength_nm, material)
        T_internal = np.exp(-α * thickness_cm)
        
        # Apply Fresnel losses
        T_fresnel = self._fresnel_loss(n)
        transmission = T_internal * T_fresnel * material.peak_transmission
        
        # Apply defects
        if defects:
            for defect_key in defects:
                if defect_key in self.defects:
                    transmission = self._apply_defect(
                        transmission, wavelength_nm, self.defects[defect_key]
                    )
        
        # Add measurement noise
        noise = self.rng.normal(0, noise_level, len(wavelength_nm))
        transmission = np.clip(transmission + noise, 0, 1)
        
        # Convert to percentage
        transmission_percent = transmission * 100
        
        return pd.DataFrame({
            'wavelength_nm': wavelength_nm,
            'transmission_percent': transmission_percent,
            'material_type': material.name,
            'material_key': material_key,
            'thickness_mm': thickness_mm,
            'has_defects': bool(defects),
            'defect_types': ','.join(defects) if defects else 'none'
        })
    
    def generate_dataset(
        self,
        n_samples_per_material: int = 10,
        defect_probability: float = 0.3,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Generate a complete dataset with multiple materials and samples.
        
        Args:
            n_samples_per_material: Samples per material type
            defect_probability: Probability of including defects
            output_path: Optional path to save CSV
            
        Returns:
            Combined DataFrame of all spectra
        """
        all_spectra = []
        sample_id = 0
        
        for material_key in self.materials:
            logger.info(f"Generating {n_samples_per_material} samples for {material_key}")
            
            for i in range(n_samples_per_material):
                # Vary thickness realistically
                thickness = self.rng.uniform(1.0, 5.0)
                
                # Randomly apply defects
                defects = None
                if self.rng.random() < defect_probability:
                    n_defects = self.rng.integers(1, 3)
                    defects = list(self.rng.choice(
                        list(self.defects.keys()), 
                        size=n_defects, 
                        replace=False
                    ))
                
                spectrum = self.generate_spectrum(
                    material_key=material_key,
                    thickness_mm=thickness,
                    defects=defects,
                    noise_level=self.rng.uniform(0.003, 0.010)
                )
                spectrum['sample_id'] = f"{material_key}_{sample_id:04d}"
                all_spectra.append(spectrum)
                sample_id += 1
        
        dataset = pd.concat(all_spectra, ignore_index=True)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            dataset.to_csv(output_path, index=False)
            logger.info(f"Saved dataset to {output_path}")
        
        return dataset


def main():
    """Generate sample datasets for the Optical Spectrum Analyzer."""
    generator = SpectroscopyDataGenerator(seed=42)
    
    # Generate main dataset
    print("="*60)
    print("OPTICAL SPECTRUM ANALYZER - DATA GENERATOR")
    print("="*60)
    print("\nGenerating synthetic spectroscopy dataset...")
    print("Based on real optical constants from RefractiveIndex.INFO")
    print()
    
    # Use project root for output
    output_path = PROJECT_ROOT / "data" / "generated" / "optical_transmission_data.csv"
    
    dataset = generator.generate_dataset(
        n_samples_per_material=15,
        defect_probability=0.25,
        output_path=output_path
    )
    
    print(f"\n✓ Generated {len(dataset)} total data points")
    print(f"✓ {dataset['sample_id'].nunique()} unique samples")
    print(f"✓ {dataset['material_type'].nunique()} material types")
    
    # Summary statistics
    print("\nMaterial Summary:")
    print("-" * 40)
    for material in dataset['material_type'].unique():
        mat_data = dataset[dataset['material_type'] == material]
        n_samples = mat_data['sample_id'].nunique()
        n_defective = mat_data[mat_data['has_defects']]['sample_id'].nunique()
        avg_trans = mat_data['transmission_percent'].mean()
        print(f"  {material}: {n_samples} samples ({n_defective} defective), "
              f"avg transmission: {avg_trans:.1f}%")
    
    print("\n" + "="*60)
    print("Data generation complete!")
    print("="*60)


if __name__ == "__main__":
    main()