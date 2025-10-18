%% MATERIAL_PROPERTIES.M
% Database of optical material properties for transmission simulation
%
% Contains wavelength-dependent absorption coefficients and Sellmeier
% coefficients for refractive index calculation.
%
% Data sources:
%   - RefractiveIndex.INFO database (Polyanskiy, 2024)
%   - Malitson, I.H. (1965) J. Opt. Soc. Am. 55, 1205-1208
%   - SCHOTT AG optical glass datasheets
%   - Crystran Ltd optical materials handbook
%
% Author: Kuldeep Choksi

function materials = material_properties()
    % MATERIAL_PROPERTIES Returns a struct with optical properties
    %
    % Output:
    %   materials - Struct containing properties for each material
    %
    % Each material contains:
    %   .name           - Full material name
    %   .formula        - Chemical formula
    %   .sellmeier      - Sellmeier coefficients [B1 B2 B3 C1 C2 C3]
    %   .uv_cutoff      - UV transmission cutoff (nm)
    %   .ir_cutoff      - IR transmission cutoff (nm)
    %   .alpha_base     - Base absorption coefficient at 550nm (cm^-1)
    %   .peak_trans     - Peak internal transmission (0-1)
    %   .reference      - Data source reference
    
    %% Sapphire (Al2O3) - Single crystal corundum
    % Excellent UV to mid-IR transmission, very hard
    % Reference: Malitson & Dodge (1972)
    materials.sapphire.name = 'Sapphire (Al2O3)';
    materials.sapphire.formula = 'Al2O3';
    materials.sapphire.sellmeier = [1.4313493, 0.65054713, 5.3414021, ...
                                    0.0052799261, 0.0142382647, 325.01783];
    materials.sapphire.uv_cutoff = 170;    % nm
    materials.sapphire.ir_cutoff = 5500;   % nm
    materials.sapphire.alpha_base = 0.003; % cm^-1
    materials.sapphire.peak_trans = 0.93;
    materials.sapphire.reference = 'Malitson & Dodge (1972)';
    
    %% Fused Silica (SiO2) - Amorphous silicon dioxide
    % Excellent UV transmission, standard reference material
    % Reference: Malitson (1965) J. Opt. Soc. Am. 55, 1205-1208
    materials.fused_silica.name = 'Fused Silica (SiO2)';
    materials.fused_silica.formula = 'SiO2';
    materials.fused_silica.sellmeier = [0.6961663, 0.4079426, 0.8974794, ...
                                        0.0046791, 0.0135121, 97.9340];
    materials.fused_silica.uv_cutoff = 180;
    materials.fused_silica.ir_cutoff = 3500;
    materials.fused_silica.alpha_base = 0.001;
    materials.fused_silica.peak_trans = 0.935;
    materials.fused_silica.reference = 'Malitson (1965)';
    
    %% N-BK7 Borosilicate Crown Glass
    % Standard optical glass, visible/NIR applications
    % Reference: SCHOTT AG datasheet
    materials.bk7.name = 'Borosilicate Crown (N-BK7)';
    materials.bk7.formula = 'SiO2-B2O3';
    materials.bk7.sellmeier = [1.03961212, 0.231792344, 1.01046945, ...
                               0.00600069867, 0.0200179144, 103.560653];
    materials.bk7.uv_cutoff = 350;
    materials.bk7.ir_cutoff = 2500;
    materials.bk7.alpha_base = 0.005;
    materials.bk7.peak_trans = 0.92;
    materials.bk7.reference = 'SCHOTT AG N-BK7';
    
    %% Calcium Fluoride (CaF2)
    % Wide transmission range, UV to far-IR
    % Reference: RefractiveIndex.INFO
    materials.caf2.name = 'Calcium Fluoride (CaF2)';
    materials.caf2.formula = 'CaF2';
    materials.caf2.sellmeier = [0.5675888, 0.4710914, 3.8484723, ...
                                0.00252643, 0.01007833, 1200.556];
    materials.caf2.uv_cutoff = 130;
    materials.caf2.ir_cutoff = 10000;
    materials.caf2.alpha_base = 0.0005;
    materials.caf2.peak_trans = 0.95;
    materials.caf2.reference = 'RefractiveIndex.INFO';
    
    %% Soda-Lime Glass
    % Standard window glass, limited UV
    materials.soda_lime.name = 'Soda-Lime Glass';
    materials.soda_lime.formula = 'SiO2-Na2O-CaO';
    materials.soda_lime.sellmeier = [1.0, 0.2, 0.9, 0.006, 0.02, 100];
    materials.soda_lime.uv_cutoff = 320;
    materials.soda_lime.ir_cutoff = 2200;
    materials.soda_lime.alpha_base = 0.015;
    materials.soda_lime.peak_trans = 0.89;
    materials.soda_lime.reference = 'Generic float glass';
    
    %% Zinc Selenide (ZnSe)
    % IR optical material, CO2 laser windows
    materials.znse.name = 'Zinc Selenide (ZnSe)';
    materials.znse.formula = 'ZnSe';
    materials.znse.sellmeier = [4.2980, 0.62776, 2.8955, ...
                                0.1036, 0.2665, 2575.0];
    materials.znse.uv_cutoff = 550;
    materials.znse.ir_cutoff = 18000;
    materials.znse.alpha_base = 0.0005;
    materials.znse.peak_trans = 0.71;
    materials.znse.reference = 'RefractiveIndex.INFO';
end

function n = calculate_refractive_index(wavelength_um, sellmeier)
    % CALCULATE_REFRACTIVE_INDEX Using Sellmeier equation
    %
    % Inputs:
    %   wavelength_um - Wavelength in micrometers
    %   sellmeier     - [B1 B2 B3 C1 C2 C3] coefficients
    %
    % Output:
    %   n - Refractive index at given wavelength(s)
    %
    % Sellmeier equation:
    %   n^2 - 1 = B1*λ²/(λ²-C1) + B2*λ²/(λ²-C2) + B3*λ²/(λ²-C3)
    
    B1 = sellmeier(1); B2 = sellmeier(2); B3 = sellmeier(3);
    C1 = sellmeier(4); C2 = sellmeier(5); C3 = sellmeier(6);
    
    lambda_sq = wavelength_um.^2;
    
    n_sq = 1 + (B1 .* lambda_sq) ./ (lambda_sq - C1) + ...
               (B2 .* lambda_sq) ./ (lambda_sq - C2) + ...
               (B3 .* lambda_sq) ./ (lambda_sq - C3);
    
    n = sqrt(max(n_sq, 1));  % Ensure positive
end

function alpha = calculate_absorption_coefficient(wavelength_nm, material)
    % CALCULATE_ABSORPTION_COEFFICIENT Wavelength-dependent absorption
    %
    % Models:
    %   - Urbach tail absorption near UV edge
    %   - Multiphonon absorption near IR edge
    %   - Constant absorption in transparent region
    %
    % Inputs:
    %   wavelength_nm - Wavelength array in nanometers
    %   material      - Material struct from material_properties()
    %
    % Output:
    %   alpha - Absorption coefficient (cm^-1)
    
    uv_cutoff = material.uv_cutoff;
    ir_cutoff = material.ir_cutoff;
    alpha_base = material.alpha_base;
    
    % Base absorption
    alpha = ones(size(wavelength_nm)) * alpha_base;
    
    % UV absorption edge (Urbach tail)
    uv_region = wavelength_nm < (uv_cutoff + 50);
    alpha(uv_region) = alpha(uv_region) + ...
        exp((uv_cutoff - wavelength_nm(uv_region)) / 20) * 0.5;
    
    % IR absorption edge (multiphonon)
    ir_region = wavelength_nm > (ir_cutoff - 200);
    alpha(ir_region) = alpha(ir_region) + ...
        exp((wavelength_nm(ir_region) - ir_cutoff) / 100) * 0.3;
end