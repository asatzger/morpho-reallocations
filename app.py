import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_table
import dash_bootstrap_components as dbc

# Load the data
file_path = 'Morpho Blue Reallocations - Raw data - Public reallocations.csv'
data = pd.read_csv(file_path)

# Coerce numeric columns to numeric to avoid casting as string
numeric_columns = ['assets', 'blockNumber', 'vault.asset.decimals', 'borrow rate (t)', 'borrow rate (t-1)']
data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Convert the 'market.lltv' column to numeric values
data['market.lltv'] = data['market.lltv'].str.replace(',', '').astype(float)

# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Transaction Pairs Dashboard", className="text-center mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Vault"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='name-dropdown',
                        options=[{'label': name, 'value': name} for name in data['vault.name'].unique()],
                        placeholder="Select a vault name",
                        clearable=True,
                        className="mb-4"
                    )
                ])
            ]),
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Strategies"),
                dbc.CardBody([
                    dbc.Checklist(
                        id='logical-filters',
                        options=[
                            {'label': 'Collateral Diversification', 'value': 'collateral_diversification'},
                            {'label': 'Yield Chasing', 'value': 'yield_chasing'},
                            {'label': 'LTV Reduction', 'value': 'ltv_reduction'}
                        ],
                        value=[],
                        inline=True,
                        switch=True,
                        className="mb-4"
                    )
                ])
            ])
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id='transaction-table',
                columns=[
                    {'name': 'Block Number', 'id': 'blockNumber'},
                    {'name': 'Transfer Value', 'id': 'assets_value'},
                    {'name': 'Vault Token', 'id': 'collateralAsset.symbol'},
                    {'name': 'Supply LTV', 'id': 'supply_ltv'},
                    {'name': 'Supply Asset', 'id': 'supply_asset'},
                    {'name': 'Withdraw LTV', 'id': 'withdraw_ltv'},
                    {'name': 'Withdraw Asset', 'id': 'withdraw_asset'},
                    {'name': 'Rate (%) - supplied', 'id': 'supply_rate'},
                    {'name': 'Rate (%) - withdrawn', 'id': 'withdraw_rate'},
                    {'name': 'Rates Delta (%pts)', 'id': 'rates_difference'},
                    {'name': 'Collateral Diversification', 'id': 'collateral_diversification'},
                    {'name': 'Yield Chasing', 'id': 'yield_chasing'},
                    {'name': 'LTV Reduction', 'id': 'ltv_reduction'},
                    {'name': 'Tx Hash', 'id': 'tx_hash', 'presentation': 'markdown'}
                ],
                data=[],
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_cell={
                    'padding': '5px',
                    'textAlign': 'center'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'blockNumber'},
                        'width': '15%'
                    },
                    {
                        'if': {'column_id': 'assets_value'},
                        'textAlign': 'right'
                    },
                    {
                        'if': {'column_id': 'collateralAsset.symbol'},
                        'width': '20%'
                    },
                    {
                        'if': {'column_id': 'market.collateralAsset.symbol_supply'},
                        'width': '15%'
                    },
                    {
                        'if': {'column_id': 'supply_llt'},
                        'width': '15%'
                    },
                    {
                        'if': {'column_id': 'withdraw_llt'},
                        'width': '15%'
                    },
                    {
                        'if': {'column_id': 'assets_value'},
                        'width': '20%'
                    }
                ],
                sort_action="native",  # Enable sorting
                sort_mode="multi"      # Allow multi-column sorting
            )
        ], width=12)
    ])
], fluid=True)

@app.callback(
    Output('transaction-table', 'data'),
    [Input('name-dropdown', 'value'),
     Input('logical-filters', 'value')]
)
def update_table(selected_name, logical_filters):
    if selected_name:
        filtered_data = data[data['vault.name'] == selected_name]
    else:
        filtered_data = data

    supply_data = filtered_data[filtered_data['type'] == 'Deposit']
    withdraw_data = filtered_data[filtered_data['type'] == 'Withdraw']

    merged_data = pd.merge(supply_data, withdraw_data, on='blockNumber', suffixes=('_supply', '_withdraw'))

    merged_data['collateral_diversification'] = merged_data['market.collateralAsset.symbol_supply'] != merged_data['market.collateralAsset.symbol_withdraw']
    merged_data['yield_chasing'] = (merged_data['borrow rate (t)_supply'] / 10**8) > (merged_data['borrow rate (t)_withdraw'] / 10**8)
    merged_data['ltv_reduction'] = (merged_data['market.lltv_supply'] / 10**18) < (merged_data['market.lltv_withdraw'] / 10**18)

    table_data = merged_data.apply(lambda row: {
        'blockNumber': row['blockNumber'],
        'collateralAsset.symbol': row['vault.asset.symbol_supply'],
        'supply_rate': round(row['borrow rate (t)_supply']/(10**8),2),
        'withdraw_rate': round(row['borrow rate (t-1)_withdraw']/(10**8),2),
        'rates_difference': round(row['borrow rate (t)_supply']/(10**8) - row['borrow rate (t)_withdraw']/(10**8), 2),
        'supply_ltv': round(row['market.lltv_supply'] / (10**18), 2),
        'supply_asset': row['market.collateralAsset.symbol_supply'],
        'withdraw_ltv': round(row['market.lltv_withdraw'] / (10**18), 2),
        'withdraw_asset': row['market.collateralAsset.symbol_withdraw'],
        'assets_value': round(row['assets_supply'] / 10**row['vault.asset.decimals_supply'],0),
        'collateral_diversification': row['collateral_diversification'],
        'yield_chasing': row['yield_chasing'],
        'ltv_reduction': row['ltv_reduction'],
        'tx_hash': f"[{row['hash_supply'][:10]}](https://etherscan.io/tx/{row['hash_supply']})"
    }, axis=1).tolist()

    if 'collateral_diversification' in logical_filters:
        table_data = [row for row in table_data if row['collateral_diversification']]
    if 'yield_chasing' in logical_filters:
        table_data = [row for row in table_data if row['yield_chasing']]
    if 'ltv_reduction' in logical_filters:
        table_data = [row for row in table_data if row['ltv_reduction']]

    return table_data

if __name__ == '__main__':
    app.run_server(debug=True)
