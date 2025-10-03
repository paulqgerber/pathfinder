# pathfinder
Python simulator for optimizing supply chain routes under disruptive events, using Google OR-Tools to frame shortest-path problems as Minimum-Cost-Flow Problems
<br>
<br>The program loads a global supply chain network from CSV files (GPT-generated) and randomly selects a start and end node for each run, calculating the initial optimal path via Google OR-Tools. The program then simulates a targeted disruption on that route by increasing a random edge's cost, forcing a re-calculation.
<br> The two different paths are visualized on an interactive map saved to an HTML file.

## Requirements 
Written in Python 3<br>
<br> Requirements: 
<br>
pandas
<br> ortools
<br> folium

## How to Run

1.  Install requirements
2.  Execute `main.py`
3.  Open the generated `supply_chain_map.html` file

## License
This project is licensed under the MIT License.
