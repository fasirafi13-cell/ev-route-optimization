import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import gradio as gr

G = nx.Graph()
G.add_weighted_edges_from([
    ('A', 'B', 10), ('A', 'C', 15),
    ('B', 'D', 12), ('C', 'D', 8),
    ('B', 'E', 20), ('D', 'E', 10),
    ('C', 'F', 18), ('E', 'F', 7)
], weight='distance')

stations = {
    'B': {'cost': 100, 'time': 20},
    'C': {'cost': 80, 'time': 15},
    'D': {'cost': 120, 'time': 25},
    'E': {'cost': 90, 'time': 10}
}

def dashboard(start, destination, objective):
    routes = list(nx.all_simple_paths(G, start, destination))
    results = []

    for route in routes:
        distance = 0
        cost = 0
        charging_time = 0

        for u, v in zip(route[:-1], route[1:]):
            distance += G[u][v].get('distance', G[u][v].get('weight', 1))

        for node in route:
            if node in stations:
                cost += stations[node]['cost']
                charging_time += stations[node]['time']

        results.append({
            'Route': ' -> '.join(route),
            'Distance (km)': distance,
            'Charging Cost (Rs)': cost,
            'Travel Time (min)': distance + charging_time
        })

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df, 'No route found', go.Figure()

    if objective == 'Minimum Distance':
        best = result_df.loc[result_df['Distance (km)'].idxmin()]
    elif objective == 'Minimum Cost':
        best = result_df.loc[result_df['Charging Cost (Rs)'].idxmin()]
    elif objective == 'Minimum Time':
        best = result_df.loc[result_df['Travel Time (min)'].idxmin()]
    else:
        cols = ['Distance (km)', 'Charging Cost (Rs)', 'Travel Time (min)']
        values = result_df[cols]
        normalized = (values - values.min()) / (values.max() - values.min() + 1e-9)
        best = result_df.loc[normalized.mean(axis=1).idxmin()]

    best_route = best['Route'].split(' -> ')
    pos = nx.spring_layout(G, seed=42)
    fig = go.Figure()

    for u, v in G.edges():
        fig.add_trace(go.Scatter(
            x=[pos[u][0], pos[v][0]], y=[pos[u][1], pos[v][1]],
            mode='lines', line=dict(color='gray', width=2), showlegend=False
        ))

    for u, v in zip(best_route[:-1], best_route[1:]):
        fig.add_trace(go.Scatter(
            x=[pos[u][0], pos[v][0]], y=[pos[u][1], pos[v][1]],
            mode='lines', line=dict(color='red', width=5), name='Optimal Route'
        ))

    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in G.nodes()],
        y=[pos[n][1] for n in G.nodes()],
        mode='markers+text', text=list(G.nodes()), textposition='top center',
        marker=dict(size=20, color='cyan'), showlegend=False
    ))
    fig.update_layout(title='EV Route Optimization', template='plotly_dark', height=450)

    summary = (
        f"Optimal Route: {best['Route']}\\n"
        f"Distance: {best['Distance (km)']} km\\n"
        f"Charging Cost: Rs. {best['Charging Cost (Rs)']}\\n"
        f"Travel Time: {best['Travel Time (min)']} minutes"
    )
    return result_df, summary, fig

with gr.Blocks() as demo:
    gr.Markdown('# EV Route Optimization Dashboard')
    with gr.Row():
        start = gr.Dropdown(choices=list(G.nodes()), value='A', label='Start Location')
        destination = gr.Dropdown(choices=list(G.nodes()), value='F', label='Destination')
    objective = gr.Radio(
        choices=['Balanced', 'Minimum Distance', 'Minimum Cost', 'Minimum Time'],
        value='Balanced', label='Optimization Objective'
    )
    button = gr.Button('Optimize Route')
    table = gr.Dataframe(label='Route Comparison')
    output = gr.Textbox(label='Optimal Route')
    graph = gr.Plot(label='Interactive Route Map')
    button.click(fn=dashboard, inputs=[start, destination, objective], outputs=[table, output, graph])

if __name__ == '__main__':
    demo.launch()
