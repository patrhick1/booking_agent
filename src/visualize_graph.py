
#!/usr/bin/env python3
"""
Script to visualize the LangGraph pipeline structure.
This script generates a visual representation of the agent graph flow.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the graph from main.py
from src.main import graph

def visualize_graph():
    """
    Generate and display the graph visualization.
    """
    try:
        from IPython.display import Image, display
        
        print("Generating graph visualization...")
        
        # Generate the mermaid diagram as PNG
        graph_image = graph.get_graph().draw_mermaid_png()
        
        # Display the image
        display(Image(graph_image))
        
        print("Graph visualization displayed successfully!")
        
    except ImportError:
        print("IPython not available. Saving graph as PNG file instead...")
        
        # Save the graph as a PNG file
        graph_image = graph.get_graph().draw_mermaid_png()
        
        with open("graph_visualization.png", "wb") as f:
            f.write(graph_image)
            
        print("Graph saved as 'graph_visualization.png' in the current directory")
        
    except Exception as e:
        print(f"Error generating graph visualization: {str(e)}")
        print("Trying alternative method - printing mermaid code...")
        
        try:
            # Fallback: print the mermaid code as text
            mermaid_code = graph.get_graph().draw_mermaid()
            print("\nMermaid Graph Code:")
            print("-" * 50)
            print(mermaid_code)
            print("-" * 50)
            print("\nYou can copy this code and paste it into https://mermaid.live to visualize the graph")
            
        except Exception as fallback_error:
            print(f"Fallback method also failed: {str(fallback_error)}")

if __name__ == "__main__":
    visualize_graph()
