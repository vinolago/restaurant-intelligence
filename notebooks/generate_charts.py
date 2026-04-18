import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, '..', 'data')
report_path = os.path.join(script_dir, '..', 'reports', 'charts')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Load data
daily_ops = pd.read_csv(os.path.join(data_path, 'daily_operations.csv'))
restaurants = pd.read_csv(os.path.join(data_path, 'restaurant_master.csv'))

# Merge data
df = daily_ops.merge(restaurants, left_on='restaurant_id', right_on='restaurant_id', how='left')
df['date'] = pd.to_datetime(df['date'])
df['day_of_week'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['is_weekend'] = df['day_of_week'] >= 5
df['total_cost'] = df['food_cost'] + df['staff_cost'] + df['rent'] + df['operating_expenses']
df['profit_margin'] = (df['net_profit'] / df['revenue']) * 100
df['cost_ratio'] = (df['total_cost'] / df['revenue']) * 100
df['aov'] = df['revenue'] / df['customers']

# Beverage simulation
beverage_ratios = {'CBD': 0.55, 'Airport': 0.58, 'Highway': 0.45, 'Suburb': 0.40}
df['beverage_ratio'] = df['location_tier'].map(beverage_ratios)
df['beverage_revenue_adj'] = df['revenue'] * (df['beverage_ratio'] + (df['efficiency_score'] - 0.75) * 0.1).clip(0.25, 0.75)
df['food_revenue_adj'] = df['revenue'] - df['beverage_revenue_adj']

# Branch aggregation
branch_summary = df.groupby(['restaurant_id', 'restaurant_name', 'location_tier', 'staff_count', 'base_rent', 'efficiency_score']).agg({
    'revenue': 'sum', 'net_profit': 'sum', 'total_cost': 'sum', 'customers': 'sum',
    'beverage_revenue_adj': 'sum', 'food_revenue_adj': 'sum'
}).reset_index()

branch_summary['profit_margin'] = (branch_summary['net_profit'] / branch_summary['revenue']) * 100
branch_summary['cost_ratio'] = (branch_summary['total_cost'] / branch_summary['revenue']) * 100
branch_summary['aov'] = branch_summary['revenue'] / branch_summary['customers']
branch_summary['beverage_ratio'] = branch_summary['beverage_revenue_adj'] / branch_summary['revenue']
branch_summary['profit_rank'] = branch_summary['net_profit'].rank(ascending=False).astype(int)

# Create output directory
os.makedirs(report_path, exist_ok=True)

# 1. Profit by Branch
fig, ax = plt.subplots(figsize=(14, 6))
branch_sorted = branch_summary.sort_values('net_profit', ascending=True)
colors = ['#e74c3c' if x < 0 else '#27ae60' for x in branch_sorted['net_profit']]
bars = ax.barh(branch_sorted['restaurant_name'], branch_sorted['net_profit']/1e6, color=colors)
ax.set_xlabel('Net Profit (Million KES)', fontsize=12)
ax.set_title('Branch Profitability Ranking', fontsize=14, fontweight='bold')
ax.axvline(x=0, color='black', linewidth=0.8)
for bar, profit in zip(bars, branch_sorted['net_profit']):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f'{profit/1e6:.1f}M', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'profit_by_branch.png'), dpi=150, bbox_inches='tight')
plt.close()
print('1. profit_by_branch.png created')

# 2. Revenue vs Cost Scatter
fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(branch_summary['total_cost']/1e6, branch_summary['revenue']/1e6, 
    s=branch_summary['profit_margin']*10, alpha=0.7, c=branch_summary['profit_margin'], cmap='RdYlGn',
    edgecolors='black', linewidth=1)
ax.plot([0, branch_summary['total_cost'].max()/1e6*1.2], 
    [0, branch_summary['total_cost'].max()/1e6*1.2], 'k--', alpha=0.5, label='Break-even line')
ax.set_xlabel('Total Cost (Million KES)', fontsize=12)
ax.set_ylabel('Total Revenue (Million KES)', fontsize=12)
ax.set_title('Revenue vs Cost Analysis', fontsize=14, fontweight='bold')
for _, row in branch_summary.iterrows():
    ax.annotate(row['restaurant_name'].replace('Java House ', ''), 
        (row['total_cost']/1e6, row['revenue']/1e6), xytext=(5, 5), textcoords='offset points', fontsize=8)
plt.colorbar(scatter, label='Profit Margin %')
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'revenue_vs_cost_scatter.png'), dpi=150, bbox_inches='tight')
plt.close()
print('2. revenue_vs_cost_scatter.png created')

# 3. Profit Margin by Location Type
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
location_stats = branch_summary.groupby('location_tier').agg({'revenue': 'mean', 'net_profit': 'mean', 'profit_margin': 'mean', 'total_cost': 'mean'}).round(2)
locations = location_stats.index.tolist()
x = np.arange(len(locations))
width = 0.35
axes[0].bar(x - width/2, location_stats['revenue']/1e6, width, label='Revenue', color='#3498db')
axes[0].bar(x + width/2, location_stats['total_cost']/1e6, width, label='Total Cost', color='#e74c3c')
axes[0].set_xlabel('Location Type')
axes[0].set_ylabel('Amount (Million KES)')
axes[0].set_title('Average Revenue vs Cost by Location')
axes[0].set_xticks(x)
axes[0].set_xticklabels(locations)
axes[0].legend()
colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(locations)))
axes[1].bar(locations, location_stats['profit_margin'], color=colors)
axes[1].set_xlabel('Location Type')
axes[1].set_ylabel('Profit Margin %')
axes[1].set_title('Average Profit Margin by Location Type')
axes[1].axhline(y=branch_summary['profit_margin'].mean(), color='gray', linestyle='--', label='Overall Avg')
for i, v in enumerate(location_stats['profit_margin']):
    axes[1].text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'profit_margin_by_location_type.png'), dpi=150, bbox_inches='tight')
plt.close()
print('3. profit_margin_by_location_type.png created')

# 4. Beverage vs Profit Correlation
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].scatter(branch_summary['beverage_ratio']*100, branch_summary['profit_margin'], 
    s=branch_summary['revenue']/5e6, alpha=0.7, c='purple', edgecolors='black')
axes[0].set_xlabel('Beverage Revenue Ratio (%)', fontsize=12)
axes[0].set_ylabel('Profit Margin (%)', fontsize=12)
axes[0].set_title('Beverage Ratio vs Profit Margin', fontsize=14, fontweight='bold')
z = np.polyfit(branch_summary['beverage_ratio']*100, branch_summary['profit_margin'], 1)
p = np.poly1d(z)
x_line = np.linspace(branch_summary['beverage_ratio'].min()*100, branch_summary['beverage_ratio'].max()*100, 100)
axes[0].plot(x_line, p(x_line), 'r--', alpha=0.7, label=f'Trend: y = {z[0]:.2f}x + {z[1]:.1f}')
axes[0].legend()
branch_summary['beverage_category'] = pd.cut(branch_summary['beverage_ratio'], bins=[0, 0.45, 0.55, 1], labels=['Low (<45%)', 'Medium (45-55%)', 'High (>55%)'])
beverage_comp = branch_summary.groupby('beverage_category')['profit_margin'].mean()
colors = ['#e74c3c', '#f39c12', '#27ae60']
axes[1].bar(beverage_comp.index, beverage_comp.values, color=colors)
axes[1].set_xlabel('Beverage Revenue Category')
axes[1].set_ylabel('Average Profit Margin %')
axes[1].set_title('Profit Margin by Beverage Mix', fontsize=14, fontweight='bold')
for bar in axes[1].containers[0]:
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{bar.get_height():.1f}%', ha='center', fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'beverage_vs_profit_correlation.png'), dpi=150, bbox_inches='tight')
plt.close()
print('4. beverage_vs_profit_correlation.png created')

# 5. Peak Hour/Day Pattern
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
daily_pattern = df.groupby('day_of_week').agg({'revenue': 'mean', 'customers': 'mean', 'net_profit': 'mean'}).reset_index()
day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
daily_pattern['day_name'] = daily_pattern['day_of_week'].map(lambda x: day_names[x])
axes[0].plot(daily_pattern['day_name'], daily_pattern['revenue']/1e3, 'b-o', linewidth=2, markersize=8, label='Revenue')
axes[0].set_xlabel('Day of Week')
axes[0].set_ylabel('Average Revenue (Thousands KES)', color='blue')
axes[0].tick_params(axis='y', labelcolor='blue')
ax1b = axes[0].twinx()
ax1b.plot(daily_pattern['day_name'], daily_pattern['net_profit']/1e3, 'g-s', linewidth=2, markersize=8, label='Profit')
ax1b.set_ylabel('Average Profit (Thousands KES)', color='green')
axes[0].set_title('Daily Revenue & Profit Pattern', fontsize=14, fontweight='bold')
monthly_pattern = df.groupby('month').agg({'revenue': 'mean', 'net_profit': 'mean'}).reset_index()
axes[1].bar(monthly_pattern['month'], monthly_pattern['revenue']/1e3, alpha=0.7, label='Revenue', color='#3498db')
axes[1].bar(monthly_pattern['month'], monthly_pattern['net_profit']/1e3, alpha=0.7, label='Profit', color='#27ae60')
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Amount (Thousands KES)')
axes[1].set_title('Monthly Revenue & Profit Trend', fontsize=14, fontweight='bold')
axes[1].legend()
axes[1].set_xticks(range(1, 13))
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'peak_hour_heatmap.png'), dpi=150, bbox_inches='tight')
plt.close()
print('5. peak_hour_heatmap.png created')

# 6. Category Revenue Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
category_revenue = branch_summary[['restaurant_name', 'beverage_revenue_adj', 'food_revenue_adj']].copy().sort_values('beverage_revenue_adj', ascending=False)
x = np.arange(len(category_revenue))
width = 0.35
axes[0].bar(x - width/2, category_revenue['beverage_revenue_adj']/1e6, width, label='Beverage Revenue', color='#8e44ad')
axes[0].bar(x + width/2, category_revenue['food_revenue_adj']/1e6, width, label='Food Revenue', color='#e67e22')
axes[0].set_xlabel('Branch')
axes[0].set_ylabel('Revenue (Million KES)')
axes[0].set_title('Beverage vs Food Revenue by Branch', fontsize=14, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels([n.replace('Java House ', '') for n in category_revenue['restaurant_name']], rotation=90, fontsize=8)
axes[0].legend()
total_beverage = branch_summary['beverage_revenue_adj'].sum()
total_food = branch_summary['food_revenue_adj'].sum()
axes[1].pie([total_beverage, total_food], labels=['Beverages', 'Food'], colors=['#8e44ad', '#e67e22'], autopct='%1.1f%%', shadow=True, startangle=90)
axes[1].set_title('Total Revenue Mix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'category_revenue_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print('6. category_revenue_distribution.png created')

# 7. Cost Ratio by Branch
fig, ax = plt.subplots(figsize=(14, 6))
branch_sorted = branch_summary.sort_values('cost_ratio', ascending=False)
colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(branch_sorted)))
ax.bar(range(len(branch_sorted)), branch_sorted['cost_ratio'], color=colors)
ax.set_xticks(range(len(branch_sorted)))
ax.set_xticklabels([n.replace('Java House ', '') for n in branch_sorted['restaurant_name']], rotation=90)
ax.set_xlabel('Branch')
ax.set_ylabel('Cost Ratio (%)')
ax.set_title('Cost Efficiency by Branch', fontsize=14, fontweight='bold')
ax.axhline(y=branch_summary['cost_ratio'].mean(), color='red', linestyle='--', linewidth=2, label='Average')
ax.legend()
for i, (idx, row) in enumerate(branch_sorted.iterrows()):
    ax.text(i, row['cost_ratio'] + 1, f'{row["cost_ratio"]:.1f}%', ha='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'cost_ratio_by_branch.png'), dpi=150, bbox_inches='tight')
plt.close()
print('7. cost_ratio_by_branch.png created')

# 8. Top vs Bottom Branches
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
top5 = branch_summary.nlargest(5, 'net_profit')
bottom5 = branch_summary.nsmallest(5, 'net_profit')
comparison = pd.concat([top5, bottom5]).sort_values('net_profit', ascending=True)
colors = ['#e74c3c' if x < 0 else '#27ae60' for x in comparison['net_profit']]
axes[0].barh(range(len(comparison)), comparison['net_profit']/1e6, color=colors)
axes[0].set_yticks(range(len(comparison)))
axes[0].set_yticklabels([n.replace('Java House ', '') for n in comparison['restaurant_name']])
axes[0].set_xlabel('Net Profit (Million KES)')
axes[0].set_title('Top 5 vs Bottom 5 Branches by Profit', fontsize=14, fontweight='bold')
axes[0].axvline(x=0, color='black', linewidth=0.8)
metrics = ['profit_margin', 'beverage_ratio', 'cost_ratio', 'efficiency_score']
metric_names = ['Profit Margin', 'Beverage Ratio', 'Cost Ratio', 'Efficiency']
x = np.arange(len(metrics))
width = 0.35
top_vals = [top5[m].mean() * (100 if m == 'profit_margin' else 1) for m in metrics]
bottom_vals = [bottom5[m].mean() * (100 if m == 'profit_margin' else 1) for m in metrics]
axes[1].bar(x - width/2, top_vals, width, label='Top 5', color='#27ae60')
axes[1].bar(x + width/2, bottom_vals, width, label='Bottom 5', color='#e74c3c')
axes[1].set_xticks(x)
axes[1].set_xticklabels(metric_names)
axes[1].set_ylabel('Value')
axes[1].set_title('Key Metrics: Top vs Bottom Performers', fontsize=14, fontweight='bold')
axes[1].legend()
plt.tight_layout()
plt.savefig(os.path.join(report_path, 'top_vs_bottom_branches.png'), dpi=150, bbox_inches='tight')
plt.close()
print('8. top_vs_bottom_branches.png created')

# Save branch summary CSV
branch_summary.to_csv(os.path.join(script_dir, '..', 'reports', 'branch_summary.csv'), index=False)
print('branch_summary.csv created')

# Save enriched data
df.to_csv(os.path.join(data_path, 'enriched_daily_ops.csv'), index=False)
print('enriched_daily_ops.csv created')

print('\nAll outputs generated successfully!')