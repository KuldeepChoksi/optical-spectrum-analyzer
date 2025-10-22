%% TRANSMISSION_MODEL.M
% Optical Transmission Simulation using Beer-Lambert Law
%
% This script simulates light transmission through optical materials
% accounting for:
%   1. Internal absorption (Beer-Lambert law)
%   2. Fresnel reflection losses at surfaces
%   3. Wavelength-dependent effects
%
% Physics:
%   Beer-Lambert Law: T = exp(-α * d)
%   where:
%     T = Internal transmission (0-1)
%     α = Absorption coefficient (cm^-1)
%     d = Material thickness (cm)
%
%   Fresnel Loss (normal incidence):
%     R = ((n-1)/(n+1))^2
%     Total transmission = T_internal * (1-R)^2
%
% Author: Kuldeep Choksi
% Based on optical constants from RefractiveIndex.INFO

clear; clc; close all;

%% Configuration
% Wavelength range (nm)
wavelength_nm = 200:2:2500;
wavelength_um = wavelength_nm / 1000;

% Sample thickness (mm)
thickness_mm = 2.0;
thickness_cm = thickness_mm / 10;

%% Load Material Properties
materials = material_properties();

%% Select Material for Simulation
% Choose from: 'sapphire', 'fused_silica', 'bk7', 'caf2', 'soda_lime', 'znse'
material_key = 'fused_silica';
mat = materials.(material_key);

fprintf('===========================================\n');
fprintf('OPTICAL TRANSMISSION SIMULATION\n');
fprintf('===========================================\n');
fprintf('Material: %s\n', mat.name);
fprintf('Formula: %s\n', mat.formula);
fprintf('Thickness: %.2f mm\n', thickness_mm);
fprintf('Wavelength range: %d - %d nm\n', min(wavelength_nm), max(wavelength_nm));
fprintf('Reference: %s\n', mat.reference);
fprintf('-------------------------------------------\n');

%% Calculate Refractive Index (Sellmeier Equation)
% n^2 - 1 = Σ (Bi * λ²) / (λ² - Ci)
n = calculate_sellmeier(wavelength_um, mat.sellmeier);

fprintf('Refractive index at 550nm: %.4f\n', interp1(wavelength_nm, n, 550));

%% Calculate Absorption Coefficient
% Includes UV/IR absorption edges
alpha = calculate_absorption(wavelength_nm, mat);

%% Beer-Lambert Law - Internal Transmission
% T = exp(-α * d)
T_internal = exp(-alpha * thickness_cm);

%% Fresnel Reflection Losses
% At normal incidence: R = ((n-1)/(n+1))^2
% Two surfaces: T_fresnel = (1-R)^2
R = ((n - 1) ./ (n + 1)).^2;
T_fresnel = (1 - R).^2;

%% Total Transmission
T_total = T_internal .* T_fresnel * mat.peak_trans;

% Convert to percentage
T_percent = T_total * 100;

%% Display Results
[max_T, idx_max] = max(T_percent);
fprintf('Peak transmission: %.1f%% at %d nm\n', max_T, wavelength_nm(idx_max));

% Average in visible range (400-700 nm)
vis_mask = (wavelength_nm >= 400) & (wavelength_nm <= 700);
avg_visible = mean(T_percent(vis_mask));
fprintf('Average visible transmission: %.1f%%\n', avg_visible);

%% Plot Results
figure('Position', [100, 100, 1200, 500]);

% Subplot 1: Full transmission spectrum
subplot(1, 2, 1);
plot(wavelength_nm, T_percent, 'b-', 'LineWidth', 1.5);
hold on;

% Mark spectral regions
regions = struct('UV', [200 400], 'Visible', [400 700], ...
                 'NIR', [700 1400], 'MIR', [1400 2500]);
colors = {'#9b59b6', '#f1c40f', '#e74c3c', '#c0392b'};
region_names = {'UV', 'Visible', 'NIR', 'MIR'};

for i = 1:length(region_names)
    range = regions.(region_names{i});
    patch([range(1) range(2) range(2) range(1)], ...
          [0 0 105 105], colors{i}, 'FaceAlpha', 0.1, 'EdgeColor', 'none');
end

% Quality thresholds
yline(90, '--g', 'Excellent', 'LineWidth', 0.8);
yline(80, '--', 'Color', [1 0.6 0], 'Label', 'Good', 'LineWidth', 0.8);
yline(70, '--r', 'Fair', 'LineWidth', 0.8);

xlabel('Wavelength (nm)');
ylabel('Transmission (%)');
title(sprintf('%s Transmission (%.1f mm)', mat.name, thickness_mm));
ylim([0 105]);
xlim([min(wavelength_nm) max(wavelength_nm)]);
grid on;
legend('Transmission', 'Location', 'best');

% Subplot 2: Refractive index and absorption
subplot(1, 2, 2);
yyaxis left;
plot(wavelength_nm, n, 'b-', 'LineWidth', 1.5);
ylabel('Refractive Index (n)');
ylim([min(n)*0.95, max(n)*1.05]);

yyaxis right;
semilogy(wavelength_nm, alpha, 'r-', 'LineWidth', 1.5);
ylabel('Absorption Coefficient (cm^{-1})');

xlabel('Wavelength (nm)');
title('Optical Constants');
grid on;
legend('n', '\alpha', 'Location', 'best');

sgtitle(sprintf('Optical Transmission Analysis: %s', mat.name), ...
        'FontSize', 14, 'FontWeight', 'bold');

%% Save Plot
saveas(gcf, sprintf('results/transmission_%s.png', material_key));
fprintf('\nPlot saved to results/transmission_%s.png\n', material_key);

%% Export Data to CSV
T_data = table(wavelength_nm', T_percent', n', alpha', ...
               'VariableNames', {'wavelength_nm', 'transmission_pct', ...
                                 'refractive_index', 'absorption_coef'});
writetable(T_data, sprintf('results/transmission_data_%s.csv', material_key));
fprintf('Data saved to results/transmission_data_%s.csv\n', material_key);

%% Helper Functions
function n = calculate_sellmeier(wavelength_um, coeffs)
    % Sellmeier dispersion equation for refractive index
    B1 = coeffs(1); B2 = coeffs(2); B3 = coeffs(3);
    C1 = coeffs(4); C2 = coeffs(5); C3 = coeffs(6);
    
    lam2 = wavelength_um.^2;
    
    n_sq = 1 + (B1 * lam2) ./ (lam2 - C1) + ...
               (B2 * lam2) ./ (lam2 - C2) + ...
               (B3 * lam2) ./ (lam2 - C3);
    
    n = sqrt(max(n_sq, 1));
end

function alpha = calculate_absorption(wavelength_nm, mat)
    % Wavelength-dependent absorption coefficient
    uv_cutoff = mat.uv_cutoff;
    ir_cutoff = mat.ir_cutoff;
    alpha_base = mat.alpha_base;
    
    alpha = ones(size(wavelength_nm)) * alpha_base;
    
    % UV edge (Urbach tail)
    uv_region = wavelength_nm < (uv_cutoff + 50);
    alpha(uv_region) = alpha(uv_region) + ...
        exp((uv_cutoff - wavelength_nm(uv_region)) / 20) * 0.5;
    
    % IR edge (multiphonon)
    ir_region = wavelength_nm > (ir_cutoff - 200);
    alpha(ir_region) = alpha(ir_region) + ...
        exp((wavelength_nm(ir_region) - ir_cutoff) / 100) * 0.3;
end