# using Pkg
# Pkg.add("DataFrames")
# Pkg.add("XLSX")

using DataFrames
using XLSX
using Plots

# function my_counterfactual_fn(df::DataFrame)
#     df.s_1_new = df.s_1 .- 0.1
#     df.s_2_new = df.s_2
#     df.s_3_new = df.s_3 .+ 0.1
#     return df
# end

# function my_counterfactual_fn(df::DataFrame)
#     df.s_1_new = df.s_1 .* 0.5
#     df.s_2_new = df.s_2 .+ 0.25 .* df.s_1
#     df.s_3_new = df.s_3 .+ 0.25 .* df.s_1
#     return df
# end

function my_counterfactual_fn(df::DataFrame)
    df.s_1_new = df.s_1_new .* 0
    df.s_2_new = df.s_2 .+ 0.5 .* df.s_1_new
    df.s_3_new = df.s_3 .+ 0.5 .* df.s_1_new
    return df
end


# Function from earlier to run counterfactual simulation
function run_counterfactual(structure_df::DataFrame,
    counterfactual_df::DataFrame,
    params_df::DataFrame)

df = innerjoin(structure_df, counterfactual_df, population_df, params_df, on=[:age, :year, :sex])

# x_1 using new equation
denominator = df.s_1 .+ df.s_2 .* df.s_n .+ df.s_3 .* df.s_n .* df.w_s
x_1 = df.x_all ./ denominator
x_2 = df.s_n .* x_1
x_3 = df.w_s .* x_2

df = my_counterfactual_fn(df)

df.x_all_new = df.s_1_new .* x_1 .+ df.s_2_new .* x_2 .+ df.s_3_new .* x_3

# Weighted averages by year
grouped = combine(groupby(df, :year)) do sub
    pop = sub.population
    DataFrame(
        year = first(sub.year),
        weighted_x_all = sum(sub.x_all .* pop) / sum(pop),
        weighted_x_all_new = sum(sub.x_all_new .* pop) / sum(pop)
    )
end

return df, grouped
end

# 🧾 Load Excel file
function load_excel_data(filepath::String)
    structure_df = DataFrame(XLSX.readtable(filepath, "structure"))
    counterfactual_df = DataFrame(XLSX.readtable(filepath, "counterfactual"))
    params_df = DataFrame(XLSX.readtable(filepath, "parameters"))
    population_df = DataFrame(XLSX.readtable(filepath, "population"))
    return structure_df, counterfactual_df, params_df, population_df
end

# 🔁 Run everything
filepath = "demographic_counterfactual_template.xlsx"  # <-- use your path
structure_df, counterfactual_df, params_df, population_df = load_excel_data(filepath)
results, grouped = run_counterfactual(structure_df, counterfactual_df, params_df)

# Plotting
plot(grouped.year, grouped.weighted_x_all,
     label = "Observed x_all",
     title = "Weighted x_all vs Counterfactual by Year",
     xlabel = "Year", ylabel = "Probability",
     lw=2, marker=:circle)

plot!(grouped.year, grouped.weighted_x_all_new,
      label = "Counterfactual x_all_new",
      lw=2, marker=:square)

savefig("simulation_result3.png")


grouped.abs_dev = grouped.weighted_x_all_new .- grouped.weighted_x_all
plot(grouped.year, grouped.abs_dev)

grouped.rel_dev = grouped.abs_dev ./ grouped.weighted_x_all
plot(grouped.year, grouped.rel_dev)

