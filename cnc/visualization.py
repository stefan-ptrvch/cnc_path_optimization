import numpy as np
from bokeh.layouts import column, row, widgetbox
from bokeh.models import CustomJS, Slider
from bokeh.models.widgets.buttons import Button
from bokeh.plotting import figure, output_file, save, ColumnDataSource
from bokeh.palettes import Category20c_20, Category10_4
from bokeh.models.markers import Triangle


class Visualizer():
    """
    Visualizes the result of the optimization for the CNC shortest cutting tool
    travel path, using bokeh.

    Parameters
    ----------
    result : list of Line
        List of Line objects, sorted in the order that represents the
        result of the optimization.
    initial : list of Line
        List of line objects, obtained at the beginning of the
        optimization, used for comaprison.
    """

    def __init__(self, result, initial):

        self.result = result
        self.initial = initial

    def populate_plot(self, plot, data):
        """
        Adds data to the plot, like starting and endpoints of cutting, lines
        representing the cutting path and lines representnig the non-cutting
        path.

        Parameters
        ----------
        plot : bokeh figure object
            Figure object on which the content of the `data` object will be
            displayed.
        data : list of Line
            List of line objects, which have to be drawn on the figure.

        Returns
        -------
        plot : bokeh figure object
            Figure populated with data from the `data` object.
        """

        # Determine which type of line gets which color
        color_map = {
                'REF': Category20c_20[16],
                'REF1': Category20c_20[16],
                'REF2': Category20c_20[16],
                'REF3': Category20c_20[16],
                'REF4': Category20c_20[16],
                'SCRIBE_LINE': Category20c_20[0],
                'SCRIBE_LINE1': Category20c_20[0],
                'SCRIBE_LINE2': Category20c_20[1],
                'SCRIBE_LINE3': Category20c_20[2],
                'SCRIBE_LINE4': Category20c_20[3],
                'BUSBAR_LINE': Category20c_20[4],
                'BUSBAR_LINE1': Category20c_20[4],
                'BUSBAR_LINE2': Category20c_20[5],
                'BUSBAR_LINE3': Category20c_20[6],
                'BUSBAR_LINE4': Category20c_20[7],
                'EDGEDEL_LINE': Category20c_20[8],
                'EDGEDEL_LINE1': Category20c_20[8],
                'EDGEDEL_LINE2': Category20c_20[9],
                'EDGEDEL_LINE3': Category20c_20[10],
                'EDGEDEL_LINE4': Category20c_20[11]
                }

        # Color of the non cutting line
        radius = 13
        line_width = 3

        scatter_points = {}
        for line in data:
            group_name = line.get_line_type() + line.get_recipe()
            sp = line.get_starting_point()
            ep = line.get_endpoint()

            # Sort scatter points
            if group_name not in scatter_points:
                scatter_points[group_name] = {
                        'x': [sp[0], ep[0]],
                        'y': [sp[1], ep[1]]
                        }
            else:
                scatter_points[group_name]['x'].append(sp[0])
                scatter_points[group_name]['x'].append(ep[0])
                scatter_points[group_name]['y'].append(sp[1])
                scatter_points[group_name]['y'].append(ep[1])

            # Cutting line
            plot.line(
                    [sp[0], ep[0]],
                    [sp[1], ep[1]],
                    color=color_map[group_name],
                    line_width=line_width
                    )

        # Add a scatter plot for every group
        for group_name, group in scatter_points.items():
            plot.scatter(
                    group['x'],
                    group['y'],
                    color=color_map[group_name],
                    radius=radius,
                    legend=group_name
                    )

        # Add travel lines
        for line in range(len(data) - 1):
            # Get the endpoint of the current line, as well as the starting
            # point of the next line
            ep0 = data[line].get_endpoint()
            sp1 = data[line + 1].get_starting_point()

            # Plot the travel line (non-cutting line)
            plot.line(
                    [
                        ep0[0],
                        sp1[0]],
                    [
                        ep0[1],
                        sp1[1]
                        ],
                    color='black',
                    legend='Non Cutting'
                    )

        return plot

    def split_line(self, start, end, increment):
        """
        Function that generates a number of points between two points.

        Generates two vectors, which represent the X and Y coordinates between
        points `start` and `end`.

        Parameters
        ----------
        start : np.array
            Numpy array containing X and Y of the starting point.
        end : np.array
            Numpy array containing X and Y of the endpoint.
        increment : int
            Euclidian distance between two successive entries in the `start`
            and `end` points.

        Returns
        -------
        out : touple of np.arrays
            Touple where the 1st element is the X coordinates and the 2nd
            element is the Y coordinates of the line.
        """

        # Determine the number of splits of the line
        num_splits = int(np.linalg.norm(end - start)/increment)
        return (
                np.linspace(start[0], end[0], num_splits),
                np.linspace(start[1], end[1], num_splits)
                )

    def generate_tool_path(self, data, step_size):
        """
        Generates the whole trajectory of the cutting tool, with a step of
        `step_size`.

        Parameters
        ----------
        data : list of Line
            List of line objects, from which the trajectory needs to be
            generated.
        step_size : int
            The Euclidian distance between two steps of the trajectory.

        Returns
        -------
        out : touple of np.arrays
            Touple where the 1st and 2nd element represents the X and Y
            coordinates of the whole cutting tool trajectory, respectively.
        """

        lines_x = np.ndarray((0))
        lines_y = np.ndarray((0))
        for line_number in range(len(data) - 1):
            sp0 = data[line_number].get_starting_point()
            ep0 = data[line_number].get_endpoint()

            sp1 = data[line_number + 1].get_starting_point()
            ep1 = data[line_number + 1].get_endpoint()

            line = np.vstack((sp0, ep0))
            next_line = np.vstack((sp1, ep1))

            # Cutting line
            line_x, line_y = self.split_line(line[0], line[1], step_size)
            lines_x = np.hstack((lines_x, line_x))
            lines_y = np.hstack((lines_y, line_y))

            # Non cutting line
            line_x, line_y = self.split_line(line[1], next_line[0], step_size)
            lines_x = np.hstack((lines_x, line_x))
            lines_y = np.hstack((lines_y, line_y))

        # Add the last line (cutting line)
        line_x, line_y = self.split_line(
                data[-1].get_starting_point(),
                data[-1].get_endpoint(),
                step_size
                )
        lines_x = np.hstack((lines_x, line_x))
        lines_y = np.hstack((lines_y, line_y))

        return lines_x, lines_y

    def visualize(self):
        """
        Generates a plot using bokeh, which displays the initial trajectory and
        the optimized trajectory of the cutting tool.
        """

        # Tools that will be displayed on the plots
        tools = "pan,wheel_zoom,reset,save"

        # Plot displaying the optimized path
        result_plot = figure(
                plot_width=1000,
                plot_height=500,
                tools=tools,
                active_scroll='wheel_zoom')
        result_plot.title.text = "Optimized Path"

        # Plot displaying the non optimized path
        initial_plot = figure(
                plot_width=1000,
                plot_height=500,
                tools=tools,
                active_scroll='wheel_zoom')
        initial_plot.title.text = "Initial Path"

        # Add the data to the result plot
        result_plot = self.populate_plot(result_plot, self.result)
        result_plot.legend.location = "bottom_right"

        # Add the data to the initial plot
        initial_plot = self.populate_plot(initial_plot, self.initial)
        initial_plot.legend.location = "bottom_right"

        # Add cutting tool to plots
        # Generate the points on which the triangle should move on
        result_lines_x, result_lines_y = self.generate_tool_path(self.result, 1)
        initial_lines_x, initial_lines_y = self.generate_tool_path(self.initial, 1)

        # Add cutting tool triangle to optimized path
        result_triangle_position = ColumnDataSource(
                data=dict(
                    x=[result_lines_x[0]],
                    y=[result_lines_y[0]]
                    ))
        result_triangle = Triangle(
                x='x', y='y', line_color=Category10_4[3], line_width=3,
                size=20, fill_alpha=0
                )
        result_plot.add_glyph(result_triangle_position, result_triangle)

        # Add cutting tool triangle to initial path
        initial_triangle_position = ColumnDataSource(
                data=dict(
                    x=[initial_lines_x[0]],
                    y=[initial_lines_y[0]]
                    ))
        initial_triangle = Triangle(
                x='x', y='y', line_color=Category10_4[3], line_width=3,
                size=20, fill_alpha=0
                )
        initial_plot.add_glyph(initial_triangle_position, initial_triangle)

        # Add button to start moving the triangle
        button = Button(label='Start')
        result_num_steps = result_lines_x.shape[0]
        initial_num_steps = initial_lines_x.shape[0]
        num_steps = max(result_num_steps, initial_num_steps)

        # JavaScript callback which will be called once the button is pressed
        callback = CustomJS(args=dict(
            result_triangle_position=result_triangle_position,
            result_lines_x=result_lines_x,
            result_lines_y=result_lines_y,
            result_num_steps=result_num_steps,
            initial_triangle_position=initial_triangle_position,
            initial_lines_x=initial_lines_x,
            initial_lines_y=initial_lines_y,
            initial_num_steps=initial_num_steps,
            num_steps=num_steps
            ),
        code="""
            // Animate optimal path plot
            for(let i = 0; i < num_steps; i += 50) {
                setTimeout(function() {
                    if (i < result_num_steps) {
                        result_triangle_position.data['x'][0] = result_lines_x[i]
                        result_triangle_position.data['y'][0] = result_lines_y[i]
                    }

                    if (i < initial_num_steps) {
                        initial_triangle_position.data['x'][0] = initial_lines_x[i]
                        initial_triangle_position.data['y'][0] = initial_lines_y[i]
                    }

                    result_triangle_position.change.emit()
                    initial_triangle_position.change.emit()

                }, i)
            }
        """)
        # Add callback function to button, which starts the whole animation
        button.js_on_click(callback)

        # Save the plot
        result_plot = row([result_plot, button])
        plot = column([result_plot, initial_plot])
        output_file("visualization.html", title="CNC Path Optimization")
        save(plot)
