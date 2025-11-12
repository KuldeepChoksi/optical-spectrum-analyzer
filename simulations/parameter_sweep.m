%% PARAMETER_SWEEP.M
% Sensitivity Analysis for Optical Transmission Parameters
%
% This script performs parameter sweeps to analyze how material
% properties affect optical transmission:
%   1. Thickness dependence
%   2. Material comparison
%   3. Purity/impurity effects
%   4. Wavelength selection optimization
%
% Useful for:
%   - Quality control threshold determination
%   - Material selection for specific applications
%   - Manufacturing tolerance analysis
%
% Author: Kuldeep Choksi

clear; clc; close all;

%% Load Material Properties
materials = material_properties();
material_names = fieldnames(materials);

%% Analysis 1: Thickness Dependence
% How does transmission change with sample thickness?
fprintf('===========================================\n');
fprintf('ANALYSIS 1: THICKNESS DEPENDENCE\n');
fprintf('===========================================\n');

wavelength_nm = 200:2:2500;
wavelength_um = wavelength_nm / 1000;
thicknesses_mm = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0];

% Use fused silica as reference material
mat = materials.fused_silica;
n = calculate_sellmeier(wavelength_um, mat.sellmeier);
alpha = calculate_absorption(wavelength_nm, mat);

figure('Position', [100, 100, 1000, 600]);
colors = parula(length(thicknesses_mm));

for i = 1:length(thicknesses_mm)
    d_cm = thicknesses_mm(i) / 10;
    
    % Beer-Lambert
    T_internal = exp(-alpha * d_cm);
    
    % Fresnel losses
    R = ((n - 1) ./ (n + 1)).^2;
    T_fresnel = (1 - R).^2;
    
    T_total = T_internal .* T_fresnel * mat.peak_trans * 100;
    
    plot(wavelength_nm, T_total, 'Color', colors(i,:), 'LineWidth', 1.5);
    hold on;
    
    % Calculate visible average
    vis_mask = (wavelength_nm >= 400) & (wavelength_nm <= 700);
    avg_vis = mean(T_total(vis_mask));
    fprintf('Thickness %.1f mm: Avg visible T = %.1f%%\n', thicknesses_mm(i), avg_vis);
end

xlabel('Wavelength (nm)');
ylabel('Transmission (%)');
title(sprintf('%s: Transmission vs Thickness', mat.name));
legend(arrayfun(@(x) sprintf('%.1f mm', x), thicknesses_mm, 'UniformOutput', false), ...
       'Location', 'best');
ylim([0 105]);
grid on;
saveas(gcf, 'results/thickness_sweep.png');

%% Analysis 2: Material Comparison
% Compare all materials at fixed thickness
fprintf('\n===========================================\n');
fprintf('ANALYSIS 2: MATERIAL COMPARISON\n');
fprintf('===========================================\n');

thickness_mm = 2.0;
d_cm = thickness_mm / 10;

figure('Position', [100, 100, 1200, 500]);

% Define colors for each material
mat_colors = struct('sapphire', [0.12, 0.47, 0.71], ...
                   'fused_silica', [1.0, 0.5, 0.05], ...
                   'bk7', [0.17, 0.63, 0.17], ...
                   'caf2', [0.55, 0.34, 0.29], ...
                   'soda_lime', [0.84, 0.15, 0.16], ...
                   'znse', [0.89, 0.47, 0.76]);

subplot(1, 2, 1);
for i = 1:length(material_names)
    mat_key = material_names{i};
    mat = materials.(mat_key);
    
    n = calculate_sellmeier(wavelength_um, mat.sellmeier);
    alpha = calculate_absorption(wavelength_nm, mat);
    
    T_internal = exp(-alpha * d_cm);
    R = ((n - 1) ./ (n + 1)).^2;
    T_fresnel = (1 - R).^2;
    T_total = T_internal .* T_fresnel * mat.peak_trans * 100;
    
    if isfield(mat_colors, mat_key)
        c = mat_colors.(mat_key);
    else
        c = [0.5 0.5 0.5];
    end
    
    plot(wavelength_nm, T_total, 'Color', c, 'LineWidth', 1.5, ...
         'DisplayName', mat.name);
    hold on;
    
    vis_mask = (wavelength_nm >= 400) & (wavelength_nm <= 700);
    avg_vis = mean(T_total(vis_mask));
    fprintf('%s: Avg visible T = %.1f%%\n', mat.name, avg_vis);
end

xlabel('Wavelength (nm)');
ylabel('Transmission (%)');
title(sprintf('Material Comparison (%.1f mm thickness)', thickness_mm));
legend('Location', 'best');
ylim([0 105]);
xlim([200 2500]);
grid on;

% Bar chart of visible transmission
subplot(1, 2, 2);
visible_trans = zeros(length(material_names), 1);
mat_labels = cell(length(material_names), 1);

for i = 1:length(material_names)
    mat_key = material_names{i};
    mat = materials.(mat_key);
    
    n = calculate_sellmeier(wavelength_um, mat.sellmeier);
    alpha = calculate_absorption(wavelength_nm, mat);
    
    T_internal = exp(-alpha * d_cm);
    R = ((n - 1) ./ (n + 1)).^2;
    T_fresnel = (1 - R).^2;
    T_total = T_internal .* T_fresnel * mat.peak_trans * 100;
    
    vis_mask = (wavelength_nm >= 400) & (wavelength_nm <= 700);
    visible_trans(i) = mean(T_total(vis_mask));
    mat_labels{i} = mat_key;
end

bar_colors = [0.2 0.7 0.2;  % Green for high
              0.9 0.6 0.1;  % Orange for medium
              0.8 0.2 0.2]; % Red for low

b = barh(visible_trans);
yticks(1:length(mat_labels));
yticklabels(mat_labels);
xlabel('Average Visible Transmission (%)');
title('Visible Range Performance');

% Color bars by quality
for i = 1:length(visible_trans)
    if visible_trans(i) >= 90
        b.FaceColor = 'flat';
        b.CData(i,:) = [0.2 0.8 0.2];
    elseif visible_trans(i) >= 80
        b.CData(i,:) = [1.0 0.7 0.2];
    else
        b.CData(i,:) = [0.8 0.2 0.2];
    end
end

xline(90, '--g', 'Excellent');
xline(80, '--', 'Color', [1 0.6 0], 'Label', 'Good');
xlim([0 100]);
grid on;

saveas(gcf, 'results/material_comparison.png');

%% Analysis 3: Impurity Effects
% Simulate how impurities affect transmission
fprintf('\n===========================================\n');
fprintf('ANALYSIS 3: IMPURITY EFFECTS\n');
fprintf('===========================================\n');

mat = materials.fused_silica;
n = calculate_sellmeier(wavelength_um, mat.sellmeier);
alpha_pure = calculate_absorption(wavelength_nm, mat);

% Impurity levels (additional absorption at 380nm - iron impurity)
impurity_levels = [0, 0.01, 0.02, 0.05, 0.10];  % cm^-1

figure('Position', [100, 100, 800, 500]);
colors = copper(length(impurity_levels));

for i = 1:length(impurity_levels)
    imp = impurity_levels(i);
    
    % Add impurity absorption band (Gaussian at 380nm)
    imp_absorption = imp * exp(-0.5 * ((wavelength_nm - 380) / 40).^2);
    alpha_total = alpha_pure + imp_absorption;
    
    T_internal = exp(-alpha_total * d_cm);
    R = ((n - 1) ./ (n + 1)).^2;
    T_fresnel = (1 - R).^2;
    T_total = T_internal .* T_fresnel * mat.peak_trans * 100;
    
    plot(wavelength_nm, T_total, 'Color', colors(i,:), 'LineWidth', 1.5);
    hold on;
    
    vis_mask = (wavelength_nm >= 400) & (wavelength_nm <= 700);
    avg_vis = mean(T_total(vis_mask));
    fprintf('Impurity α=%.2f cm^-1: Avg visible T = %.1f%%\n', imp, avg_vis);
end

xlabel('Wavelength (nm)');
ylabel('Transmission (%)');
title(sprintf('%s: Effect of Iron Impurity', mat.name));
legend(arrayfun(@(x) sprintf('α_{imp}=%.2f cm^{-1}', x), impurity_levels, ...
       'UniformOutput', false), 'Location', 'best');
ylim([0 105]);
xlim([200 1000]);
grid on;

% Mark impurity absorption region
patch([350 410 410 350], [0 0 105 105], 'r', 'FaceAlpha', 0.1, 'EdgeColor', 'none');
text(380, 10, 'Fe^{3+}', 'HorizontalAlignment', 'center', 'Color', 'red');

saveas(gcf, 'results/impurity_analysis.png');

fprintf('\n===========================================\n');
fprintf('Parameter sweep complete!\n');
fprintf('Results saved to results/ directory\n');
fprintf('===========================================\n');

%% Helper Functions
function n = calculate_sellmeier(wavelength_um, coeffs)
    B1 = coeffs(1); B2 = coeffs(2); B3 = coeffs(3);
    C1 = coeffs(4); C2 = coeffs(5); C3 = coeffs(6);
    
    lam2 = wavelength_um.^2;
    n_sq = 1 + (B1*lam2)./(lam2-C1) + (B2*lam2)./(lam2-C2) + (B3*lam2)./(lam2-C3);
    n = sqrt(max(n_sq, 1));
end

function alpha = calculate_absorption(wavelength_nm, mat)
    alpha = ones(size(wavelength_nm)) * mat.alpha_base;
    
    uv_region = wavelength_nm < (mat.uv_cutoff + 50);
    alpha(uv_region) = alpha(uv_region) + exp((mat.uv_cutoff - wavelength_nm(uv_region))/20) * 0.5;
    
    ir_region = wavelength_nm > (mat.ir_cutoff - 200);
    alpha(ir_region) = alpha(ir_region) + exp((wavelength_nm(ir_region) - mat.ir_cutoff)/100) * 0.3;
end