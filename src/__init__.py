"""
Optical Spectrum Analyzer

A comprehensive tool for analyzing optical transmission spectra of materials
used in optical component manufacturing.

Modules:
    - data_generator: Generate synthetic spectroscopy data using Beer-Lambert law
    - data_loader: Load and validate CSV spectroscopy data
    - quality_classifier: Quality metrics and classification
    - spectrum_analyzer: Main analysis orchestration
    - visualization: Plotting functions

Author: Kuldeep Choksi
"""

__version__ = '1.0.0'
__author__ = 'Kuldeep Choksi'

from .data_loader import SpectroscopyDataLoader
from .data_generator import SpectroscopyDataGenerator, MATERIAL_DATABASE
from .quality_classifier import QualityClassifier, QualityGrade, QualityMetrics
from .spectrum_analyzer import OpticalSpectrumAnalyzer
from .visualization import SpectrumVisualizer

__all__ = [
    'SpectroscopyDataLoader',
    'SpectroscopyDataGenerator', 
    'MATERIAL_DATABASE',
    'QualityClassifier',
    'QualityGrade',
    'QualityMetrics',
    'OpticalSpectrumAnalyzer',
    'SpectrumVisualizer'
]