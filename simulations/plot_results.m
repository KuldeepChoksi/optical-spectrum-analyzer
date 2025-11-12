%% PLOT_RESULTS.M
% Visualization Functions for Optical Transmission Analysis
%
% Provides publication-quality plotting functions for:
%   - Transmission spectra with spectral regions
%   - Material comparison charts
%   - Quality assessment visualizations
%   - Export to various formats
%
% Author: Kuldeep Choksi

function plot_results()
    % Main function demonstrating visualization capabilities
    
    fprintf('===========================================\n');
    fprintf('OPTICAL TRANSMISSION VISUALIZATION\n');
    fprintf('===========================================\n');
    
    % Ensure results directory exists
    if ~exist('results', 'dir')
        mkdir('results');
    end
    
    % Run all visualization demos
    demo_spectrum_plot();
    demo_comparison_plot();
    demo_quality_chart();
    
    fprintf('\nAll plots saved to results/ directory\n');
end

function demo_spectrum_plot()
    %% Demo: Single Spectrum Plot
    fprintf('\nGenerating spectrum plot...\n');
    
    % Load materials and generate sample data
    materials = material_properties();
    mat = materials.fused_silica;
    
    wavelength_nm = 200:2:2500;
    [T_percent, n] = calculate_transmission(wavelength_nm, mat, 2.0);
    
    % Create figure
    fig = figure('Position', [100, 100, 1000, 600], 'Color', 'white');
    
    % Plot with spectral regions
    plot_spectrum_with_regions(wavelength_nm, T_percent, mat.name);
    
    % Save
    saveas(fig, 'results/demo_spectrum.png');
    fprintf('  Saved: results/demo_spectrum.png\n');
end

function demo_comparison_plot()
    %% Demo: Material Comparison
    fprintf('Generating comparison plot...\n');
    
    materials = material_properties();
    material_names = fieldnames(materials);
    wavelength_nm = 200:2:2500;
    thickness_mm = 2.0;
    
    fig = figure('Position', [100, 100, 1200, 500], 'Color', 'white');
    
    % Color map for materials
    colors = lines(length(material_names));
    
    for i = 1:length(material_names)
        mat = materials.(material_names{i});
        T_percent = calculate_transmission(wavelength_nm, mat, thickness_mm);
        
        plot(wavelength_nm, T_percent, 'Color', colors(i,:), ...
             'LineWidth', 1.5, 'DisplayName', mat.name);
        hold on;
    end
    
    % Formatting
    xlabel('Wavelength (nm)', 'FontSize', 12);
    ylabel('Transmission (%)', 'FontSize', 12);
    title(sprintf('Optical Material Comparison (%.1f mm)', thickness_mm), ...
          'FontSize', 14, 'FontWeight', 'bold');
    
    % Add quality lines
    yline(90, '--g', 'LineWidth', 1);
    yline(80, '--', 'Color', [1 0.6 0], 'LineWidth', 1);
    yline(70, '--r', 'LineWidth', 1);
    
    legend('Location', 'eastoutside');
    ylim([0 105]);
    xlim([200 2500]);
    grid on;
    set(gca, 'FontSize', 11);
    
    saveas(fig, 'results/demo_comparison.png');
    fprintf('  Saved: results/demo_comparison.png\n');
end

function demo_quality_chart()
    %% Demo: Quality Assessment Chart
    fprintf('Generating quality chart...\n');
    
    materials = material_properties();
    material_names = fieldnames(materials);
    wavelength_nm = 400:700;  % Visible range only
    
    % Calculate quality metrics
    n_materials = length(material_names);
    avg_trans = zeros(n_materials, 1);
    peak_trans = zeros(n_materials, 1);
    labels = cell(n_materials, 1);
    
    for i = 1:n_materials
        mat = materials.(material_names{i});
        T = calculate_transmission(wavelength_nm, mat, 2.0);
        
        avg_trans(i) = mean(T);
        peak_trans(i) = max(T);
        labels{i} = mat.name;
    end
    
    fig = figure('Position', [100, 100, 900, 600], 'Color', 'white');
    
    % Create bar chart
    x = 1:n_materials;
    b = bar(x, [avg_trans, peak_trans], 'grouped');
    
    % Color by quality grade
    colors_avg = zeros(n_materials, 3);
    for i = 1:n_materials
        if avg_trans(i) >= 90
            colors_avg(i,:) = [0.2, 0.8, 0.2];  % Green
        elseif avg_trans(i) >= 80
            colors_avg(i,:) = [1.0, 0.7, 0.2];  % Orange
        elseif avg_trans(i) >= 70
            colors_avg(i,:) = [1.0, 0.4, 0.2];  % Light red
        else
            colors_avg(i,:) = [0.8, 0.2, 0.2];  % Red
        end
    end
    
    b(1).FaceColor = 'flat';
    b(1).CData = colors_avg;
    b(2).FaceColor = [0.5, 0.5, 0.8];
    
    % Quality threshold lines
    yline(90, '--g', 'Excellent', 'LineWidth', 1.5, 'FontSize', 10);
    yline(80, '--', 'Color', [1 0.6 0], 'Label', 'Good', 'LineWidth', 1.5);
    yline(70, '--r', 'Fair', 'LineWidth', 1.5, 'FontSize', 10);
    
    % Formatting
    xticks(x);
    xticklabels(labels);
    xtickangle(30);
    ylabel('Transmission (%)', 'FontSize', 12);
    title('Material Quality Assessment (Visible Range)', ...
          'FontSize', 14, 'FontWeight', 'bold');
    legend({'Average', 'Peak'}, 'Location', 'northeast');
    ylim([0 105]);
    grid on;
    set(gca, 'FontSize', 11);
    
    saveas(fig, 'results/demo_quality.png');
    fprintf('  Saved: results/demo_quality.png\n');
end

function plot_spectrum_with_regions(wavelength_nm, T_percent, title_str)
    %% Plot spectrum with colored spectral regions
    
    % Define spectral regions
    regions = struct();
    regions.UV = struct('range', [200 400], 'color', [0.61 0.35 0.71], 'alpha', 0.15);
    regions.Visible = struct('range', [400 700], 'color', [0.95 0.77 0.06], 'alpha', 0.15);
    regions.NIR = struct('range', [700 1400], 'color', [0.91 0.30 0.24], 'alpha', 0.12);
    regions.MIR = struct('range', [1400 2500], 'color', [0.75 0.22 0.17], 'alpha', 0.08);
    
    region_names = fieldnames(regions);
    
    % Plot regions first
    for i = 1:length(region_names)
        reg = regions.(region_names{i});
        r = reg.range;
        if r(1) <= max(wavelength_nm) && r(2) >= min(wavelength_nm)
            patch([r(1) r(2) r(2) r(1)], [0 0 105 105], ...
                  reg.color, 'FaceAlpha', reg.alpha, 'EdgeColor', 'none');
            hold on;
        end
    end
    
    % Plot spectrum
    plot(wavelength_nm, T_percent, 'b-', 'LineWidth', 2);
    
    % Add quality reference lines
    yline(90, '--', 'Color', [0.2 0.8 0.2], 'LineWidth', 1, 'Label', 'Excellent');
    yline(80, '--', 'Color', [1 0.6 0], 'LineWidth', 1, 'Label', 'Good');
    yline(70, '--', 'Color', [0.8 0.2 0.2], 'LineWidth', 1, 'Label', 'Fair');
    
    % Formatting
    xlabel('Wavelength (nm)', 'FontSize', 12);
    ylabel('Transmission (%)', 'FontSize', 12);
    title(title_str, 'FontSize', 14, 'FontWeight', 'bold');
    ylim([0 105]);
    xlim([min(wavelength_nm) max(wavelength_nm)]);
    grid on;
    set(gca, 'FontSize', 11);
    
    % Add region labels
    text(300, 98, 'UV', 'FontSize', 10, 'Color', [0.5 0.2 0.6]);
    text(550, 98, 'Visible', 'FontSize', 10, 'Color', [0.7 0.5 0.0]);
    text(1050, 98, 'NIR', 'FontSize', 10, 'Color', [0.7 0.2 0.2]);
    text(1950, 98, 'MIR', 'FontSize', 10, 'Color', [0.6 0.15 0.1]);
end

function [T_percent, n] = calculate_transmission(wavelength_nm, mat, thickness_mm)
    %% Calculate transmission using Beer-Lambert law
    wavelength_um = wavelength_nm / 1000;
    d_cm = thickness_mm / 10;
    
    % Sellmeier equation for refractive index
    coeffs = mat.sellmeier;
    B1 = coeffs(1); B2 = coeffs(2); B3 = coeffs(3);
    C1 = coeffs(4); C2 = coeffs(5); C3 = coeffs(6);
    
    lam2 = wavelength_um.^2;
    n_sq = 1 + (B1*lam2)./(lam2-C1) + (B2*lam2)./(lam2-C2) + (B3*lam2)./(lam2-C3);
    n = sqrt(max(n_sq, 1));
    
    % Absorption coefficient
    alpha = ones(size(wavelength_nm)) * mat.alpha_base;
    uv_region = wavelength_nm < (mat.uv_cutoff + 50);
    alpha(uv_region) = alpha(uv_region) + exp((mat.uv_cutoff - wavelength_nm(uv_region))/20) * 0.5;
    ir_region = wavelength_nm > (mat.ir_cutoff - 200);
    alpha(ir_region) = alpha(ir_region) + exp((wavelength_nm(ir_region) - mat.ir_cutoff)/100) * 0.3;
    
    % Beer-Lambert
    T_internal = exp(-alpha * d_cm);
    
    % Fresnel losses
    R = ((n - 1) ./ (n + 1)).^2;
    T_fresnel = (1 - R).^2;
    
    % Total transmission
    T_percent = T_internal .* T_fresnel * mat.peak_trans * 100;
end

% Run if called directly
if ~isdeployed
    plot_results();
end