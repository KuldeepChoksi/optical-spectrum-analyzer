"""
Data Loader Module for Optical Spectrum Analyzer

Handles loading and validation of spectroscopy CSV data from optical
transmission measurements. Supports multiple file formats and provides
data quality checks before analysis.

Author: Kuldeep Choksi
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class SpectroscopyDataLoader:
    """
    Loads and validates optical transmission spectroscopy data.
    
    Expected CSV format:
        - wavelength_nm: Wavelength in nanometers
        - transmission_percent: Transmission percentage (0-100)
        - material_type: Material identifier string
    
    Optional columns:
        - sample_id: Unique sample identifier
        - thickness_mm: Sample thickness in millimeters
        - has_defects: Boolean flag for defective samples
    """
    
    REQUIRED_COLUMNS = ['wavelength_nm', 'transmission_percent', 'material_type']
    VALID_WAVELENGTH_RANGE = (190, 25000)  # nm, UV to far-IR
    VALID_TRANSMISSION_RANGE = (0, 100)    # percentage
    
    def __init__(self, validate_on_load: bool = True):
        """
        Initialize the data loader.
        
        Args:
            validate_on_load: Whether to automatically validate data after loading
        """
        self.validate_on_load = validate_on_load
        self._loaded_data: Optional[pd.DataFrame] = None
        self._validation_errors: List[str] = []
    
    def load_csv(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """
        Load spectroscopy data from a CSV file.
        
        Args:
            filepath: Path to the CSV file
            
        Returns:
            DataFrame containing the spectroscopy data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If required columns are missing or data validation fails
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        logger.info(f"Loading spectroscopy data from {filepath}")
        
        df = pd.read_csv(filepath)
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Check for required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        if self.validate_on_load:
            self._validate_data(df)
        
        self._loaded_data = df
        
        n_samples = df['sample_id'].nunique() if 'sample_id' in df.columns else 'N/A'
        logger.info(f"Loaded {len(df)} data points, "
                   f"{df['material_type'].nunique()} materials, "
                   f"{n_samples} samples")
        
        return df
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """
        Validate the loaded data for consistency and physical plausibility.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If validation fails
        """
        self._validation_errors = []
        
        # Check wavelength range
        wl_min, wl_max = df['wavelength_nm'].min(), df['wavelength_nm'].max()
        if wl_min < self.VALID_WAVELENGTH_RANGE[0]:
            self._validation_errors.append(
                f"Wavelength below valid range: {wl_min} nm"
            )
        if wl_max > self.VALID_WAVELENGTH_RANGE[1]:
            self._validation_errors.append(
                f"Wavelength above valid range: {wl_max} nm"
            )
        
        # Check transmission values
        trans_min = df['transmission_percent'].min()
        trans_max = df['transmission_percent'].max()
        
        if trans_min < self.VALID_TRANSMISSION_RANGE[0]:
            self._validation_errors.append(
                f"Negative transmission values found: {trans_min}%"
            )
        if trans_max > self.VALID_TRANSMISSION_RANGE[1]:
            self._validation_errors.append(
                f"Transmission exceeds 100%: {trans_max}%"
            )
        
        # Check for NaN values
        nan_counts = df[self.REQUIRED_COLUMNS].isna().sum()
        if nan_counts.any():
            for col, count in nan_counts.items():
                if count > 0:
                    self._validation_errors.append(
                        f"Found {count} NaN values in column '{col}'"
                    )
        
        # Log warnings but don't raise errors for minor issues
        if self._validation_errors:
            for error in self._validation_errors:
                logger.warning(f"Validation warning: {error}")
    
    def load_multiple_files(
        self, 
        filepaths: List[Union[str, Path]]
    ) -> pd.DataFrame:
        """
        Load and concatenate data from multiple CSV files.
        
        Args:
            filepaths: List of paths to CSV files
            
        Returns:
            Combined DataFrame with all spectroscopy data
        """
        dataframes = []
        
        for filepath in filepaths:
            try:
                df = self.load_csv(filepath)
                df['source_file'] = Path(filepath).name
                dataframes.append(df)
            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")
        
        if not dataframes:
            raise ValueError("No valid data files could be loaded")
        
        combined = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined {len(dataframes)} files into {len(combined)} rows")
        
        return combined
    
    def get_sample(self, sample_id: str) -> pd.DataFrame:
        """
        Get data for a specific sample.
        
        Args:
            sample_id: The sample identifier
            
        Returns:
            DataFrame with the sample's spectrum
        """
        if self._loaded_data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        if 'sample_id' not in self._loaded_data.columns:
            raise ValueError("No sample_id column in loaded data")
        
        sample_data = self._loaded_data[
            self._loaded_data['sample_id'] == sample_id
        ]
        
        if sample_data.empty:
            raise ValueError(f"Sample not found: {sample_id}")
        
        return sample_data
    
    def get_material(self, material_type: str) -> pd.DataFrame:
        """
        Get all data for a specific material type.
        
        Args:
            material_type: The material type identifier
            
        Returns:
            DataFrame with all spectra for that material
        """
        if self._loaded_data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        material_data = self._loaded_data[
            self._loaded_data['material_type'] == material_type
        ]
        
        if material_data.empty:
            raise ValueError(f"Material not found: {material_type}")
        
        return material_data
    
    def list_materials(self) -> List[str]:
        """Get list of all material types in loaded data."""
        if self._loaded_data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        return self._loaded_data['material_type'].unique().tolist()
    
    def list_samples(self) -> List[str]:
        """Get list of all sample IDs in loaded data."""
        if self._loaded_data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        if 'sample_id' not in self._loaded_data.columns:
            return []
        return self._loaded_data['sample_id'].unique().tolist()
    
    def get_summary(self) -> Dict:
        """Get summary statistics of loaded data."""
        if self._loaded_data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        df = self._loaded_data
        
        summary = {
            'total_rows': len(df),
            'n_materials': df['material_type'].nunique(),
            'materials': df['material_type'].unique().tolist(),
            'wavelength_range': (df['wavelength_nm'].min(), df['wavelength_nm'].max()),
            'transmission_range': (
                df['transmission_percent'].min(), 
                df['transmission_percent'].max()
            ),
        }
        
        if 'sample_id' in df.columns:
            summary['n_samples'] = df['sample_id'].nunique()
        
        if 'has_defects' in df.columns:
            summary['n_defective'] = df[df['has_defects']]['sample_id'].nunique()
        
        return summary


def main():
    """Test the data loader functionality."""
    loader = SpectroscopyDataLoader()
    
    # Try to load the generated dataset
    data_path = PROJECT_ROOT / "data" / "generated" / "optical_transmission_data.csv"
    
    if data_path.exists():
        df = loader.load_csv(data_path)
        
        print("\n" + "="*50)
        print("DATA LOADER TEST")
        print("="*50)
        
        summary = loader.get_summary()
        print(f"\nTotal rows: {summary['total_rows']}")
        print(f"Materials: {summary['n_materials']}")
        print(f"Samples: {summary.get('n_samples', 'N/A')}")
        print(f"Wavelength range: {summary['wavelength_range'][0]:.0f} - "
              f"{summary['wavelength_range'][1]:.0f} nm")
        print(f"Transmission range: {summary['transmission_range'][0]:.1f} - "
              f"{summary['transmission_range'][1]:.1f}%")
        
        print("\nMaterials in dataset:")
        for mat in summary['materials']:
            print(f"  - {mat}")
    else:
        print(f"Dataset not found at {data_path}")
        print("Run data_generator.py first to create the dataset.")


if __name__ == "__main__":
    main()