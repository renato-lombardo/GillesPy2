import warnings
from datetime import datetime
from gillespy2.core.gillespyError import *
import pickle

from collections import UserDict,UserList

# List of 50 hex color values used for plotting graphs
common_rgb_values = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                         '#bcbd22', '#17becf', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#00ffff', '#ff00ff',
                         '#800000', '#808000', '#008000', '#800080', '#008080', '#000080', '#ff9999', '#ffcc99',
                         '#ccff99', '#cc99ff', '#ffccff', '#62666a', '#8896bb', '#77a096', '#9d5a6c', '#9d5a6c',
                         '#eabc75', '#ff9600', '#885300', '#9172ad', '#a1b9c4', '#18749b', '#dadecf', '#c5b8a8',
                         '#000117', '#13a8fe', '#cf0060', '#04354b', '#0297a0', '#037665', '#eed284', '#442244',
                         '#ffddee', '#702afb']

def _plot_iterate(self, show_labels = True, included_species_list = []):
    import matplotlib.pyplot as plt
    for i,species in enumerate(self.data):
        if species != 'time':

            if species not in included_species_list and included_species_list:
                continue

            line_color = common_rgb_values[(i - 1) % len(common_rgb_values)]

            if show_labels:
                label = species
            else:
                label = ""

            plt.plot(self.data['time'], self.data[species], label=label,color = line_color)

def _plotplotly_iterate(trajectory, show_labels = True, trace_list = None, line_dict= None, included_species_list= []):
    '''
    Helper method for Results .plotplotly() method
    '''

    if trace_list is None:
        trace_list = []

    import plotly.graph_objs as go

    for i,species in enumerate(trajectory.data):
        if species != 'time':

            if species not in included_species_list and included_species_list:
                continue

            if line_dict is None:
                line_dict = {}

            #If number of species exceeds number of available colors, loop back through colors
            line_dict['color'] = common_rgb_values[(i-1)%len(common_rgb_values)]

            if show_labels:
                trace_list.append(
                    go.Scatter(
                        x=trajectory.data['time'],
                        y=trajectory.data[species],
                        mode='lines',
                        name=species,
                        line = line_dict
                    )
                )
            else:
                trace_list.append(
                    go.Scatter(
                        x=trajectory.data['time'],
                        y=trajectory.data[species],
                        mode='lines',
                        name=species,
                        line=line_dict,
                        showlegend=False
                    )
                )

    return trace_list

class Trajectory(UserDict):
    """ Trajectory Dict created by a gillespy2 solver containing single trajectory, extends the UserDict object.

        Attributes
        ----------
        data : UserDict
            A dictionary of trajectory values created by a solver
        model : string
            The name of the model used to create the trajectory
        solver_name : string
            The name of the solver used to create the trajectory
        rc : int
            The solver's status return code.
        status : string
            The solver status (e.g. 'Success', 'Timed Out')
        """

    def __init__(self,data,model = None,solver_name = "Undefined solver name", rc=0):

        self.data = data
        self.model = model
        self.solver_name = solver_name
        self.rc = rc
        
        status_list = {0: 'Success', 33: 'Timed Out'}
        self.status = status_list[rc]

    def __getitem__(self, key):
        if type(key) is int:
            warnings.warn("Trajectory is of type dictionary. Use trajectory['species'] instead of trajectory[0]['species'] ")
            return self
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)


class Results(UserList):
    """ List of Trajectory objects created by a gillespy2 solver, extends the UserList object.

        Attributes
        ----------
        data : UserList
            A list of Trajectory objects
        """

    def __init__(self,data):
        self.data = data

    def __getattribute__(self,key):
        if key == 'model' or key == 'solver_name' or key == 'rc'or key == 'status':
            if len(self.data)>1:
                warnings.warn("Results is of type list. Use results[i]['model'] instead of results['model'] ")
            return(getattr(Results.__getattribute__(self,key='data')[0],key))
        else: 
            return UserList.__getattribute__(self,key)

    def __getitem__(self, key):
        if key == 'data':
            return UserList.__getitem__(self,key)
        if type(key) is str and key != 'data':
            if len(self.data)>1:
                warnings.warn("Results is of type list. Use results[i]['model'] instead of results['model'] ")
            return self.data[0][key]
        else:
            return(UserList.__getitem__(self,key))
        raise KeyError(key)

    def __add__(self, other):
        combined_data = Results(data=(self.data + other.data))
        consistent_solver = combined_data._validate_solver()
        consistent_model = combined_data._validate_model()

        if consistent_solver is False:
            warnings.warn("Results objects contain Trajectory objects from multiple solvers.")

        consistent_model = combined_data._validate_model()

        if consistent_model is False:
            raise ValidationError('Results objects contain Trajectory objects from multiple models.')

        combined_data = self.data + other.data
        return Results(data=combined_data)

    def _validate_model(self, reference = None):
        is_valid = True
        if reference is not None:
            reference_model = reference
        else:
            reference_model = self.data[0].model
        for trajectory in self.data:
            if trajectory.model != reference_model:
                is_valid = False
        return is_valid

    def _validate_solver(self, reference = None):
        is_valid = True
        if reference is not None:
            reference_solver = reference
        else:
            reference_solver = self.data[0].solver_name
        for trajectory in self.data:
            if trajectory.solver_name != reference_solver:
                is_valid = False
        return is_valid

    def _validate_title(self):
        if self._validate_model():
            title_model = self.data[0].model.name
        else:
            title_model = 'Multiple Models'
        if self._validate_solver():
            title_solver = self.data[0].solver_name
        else:
            title_solver = 'Multiple Solvers'
        title = (title_model + " - " + title_solver)
        return title

    def to_csv(self, path=None, nametag=None, stamp=None):
        """ outputs the Results to one or more .csv files in a new directory.

             Attributes
            ----------
            nametag: allows the user to optionally "tag" the directory and included files. Defaults to the model name.
            path: the location for the new directory and included files. Defaults to model location.
            stamp: Allows the user to optionally "tag" the directory (not included files). Default is timestamp.
            """
        import csv
        import os

        if stamp is None:
            now = datetime.now()
            stamp=datetime.timestamp(now)
        if nametag is None:
            identifier = self._validate_title()
        else:
            identifier = nametag
        if path is None:
            directory = os.path.join(".",str(identifier)+str(stamp))
        else:
            directory = os.path.join(path,str(identifier)+str(stamp))
    #multiple trajectories
        if isinstance(self.data,list):
            os.mkdir(directory)
            for i, trajectory in enumerate(self.data):#write each CSV file
                filename = os.path.join(directory,str(identifier)+str(i)+".csv")
                field_names = []
                for species in trajectory: #build the header
                    field_names.append(species)
                with open(filename, 'w', newline = '') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(field_names) #write the header
                    for n,time in enumerate(trajectory['time']):#write all lines of the CSV file
                        this_line=[]
                        for species in trajectory: #build one line of the CSV file
                            this_line.append(trajectory[species][n])
                        csv_writer.writerow(this_line) #write one line of the CSV file

    def plot(self, index = None, xaxis_label ="Time (s)", yaxis_label ="Species Population", style="default", title = None,
             show_legend=True, multiple_graphs = False, included_species_list=[],save_png=False,figsize = (18,10)):
        """ Plots the Results using matplotlib.

        Attributes
        ----------
        index : if not none, the index of the Trajectory to be plotted
        xaxis_label : str
            the label for the x-axis
        yaxis_label : str
            the label for the y-axis
            style : str
            the matplotlib style to be used for the graph or graphs
        title : str
            the title of the graph
        multiple_graphs : bool
            if each trajectory should have its own graph or if they should overlap
        included_species_list : list
             A list of strings describing which species to include. By default displays all species.
        save_png : bool or str
            Should the graph be saved as a png file. If True, File name is title of graph. If a string is given, file
            is named after that string.
        figsize : tuple
            the size of the graph. A tuple of the form (width,height). Is (18,10) by default.


            """
        import matplotlib.pyplot as plt
        from collections import Iterable
        trajectory_list = []
        if isinstance(index,Iterable):
            for i in index:
                trajectory_list.append(self.data[i])
        elif isinstance(index,int):
                trajectory_list.append(self.data[index])
        else:
            trajectory_list = self.data

        if title is None:
            title=self._validate_title()

        if len(trajectory_list) < 2:
                multiple_graphs = False

        if multiple_graphs:

            for i,trajectory in enumerate(trajectory_list):
                result = Results(data=[trajectory])
                if isinstance(save_png, str):
                    result.plot(xaxis_label=xaxis_label, yaxis_label=yaxis_label, title=title + " " + str(i + 1), style=style,
                                                 included_species_list=included_species_list,save_png=save_png + str(i + 1),figsize=figsize)
                else:
                    result.plot(xaxis_label=xaxis_label, yaxis_label=yaxis_label, title=title + " " + str(i + 1),style=style,
                                included_species_list=included_species_list, save_png=save_png, figsize=figsize)

        else:
            try:
                plt.style.use(style)
            except:
                warnings.warn("Invalid matplotlib style. Try using one of the following {}".format(plt.style.available))
                plt.style.use("default")

            plt.figure(figsize=figsize)
            plt.title(title, fontsize=18)
            plt.xlabel(xaxis_label)
            plt.ylabel(yaxis_label)

            for i,trajectory in enumerate(trajectory_list):

                if i > 0:
                    _plot_iterate(trajectory, included_species_list=included_species_list,show_labels=False)
                else:
                    _plot_iterate(trajectory, included_species_list=included_species_list)

            if show_legend:
                plt.legend(loc='best')
            plt.plot([0], [11])

            if isinstance(save_png, str):
                plt.savefig(save_png)

            elif save_png:
                plt.savefig(title)

    def plotplotly(self, index = None, xaxis_label = "Time (s)", yaxis_label="Species Population", title = None, show_legend=True,
                   multiple_graphs = False, included_species_list=[],return_plotly_figure=False):
        """ Plots the Results using plotly. Can only be viewed in a Jupyter Notebook.

        Attributes
        ----------
        index : if not none, the index of the Trajectory to be plotted
        xaxis_label : str
            the label for the x-axis
        yaxis_label : str
            the label for the y-axis
        title : str
            the title of the graph
        multiple_graphs : bool
            if each trajectory should have its own graph or if they should overlap
        included_species_list : list
             A list of strings describing which species to include. By default displays all species.
        return_plotly_figure : bool
            whether or not to return a figure dictionary of data(graph object traces) and layout options
            which may be edited by the user.
        **plotly_args: dict
            Optional additional arguments to be passed to plotly's Layout constructor.
        """

        from plotly.offline import init_notebook_mode, iplot
        import plotly.graph_objs as go

        init_notebook_mode(connected=True)

        from collections import Iterable
        trajectory_list = []
        if isinstance(index,Iterable):
            for i in index:
                trajectory_list.append(self.data[i])
        elif isinstance(index,int):
                trajectory_list.append(self.data[index])
        else:
            trajectory_list = self.data

        number_of_trajectories =len(trajectory_list)

        if title is None:
            title=self._validate_title()

        fig = dict(data=[], layout=[])

        if len(trajectory_list) < 2:
            multiple_graphs = False

        if multiple_graphs:

            from plotly import tools

            fig = tools.make_subplots(print_grid=False,rows=int(number_of_trajectories/2) + int(number_of_trajectories%2),
                                      cols = 2)

            for i, trajectory in enumerate(trajectory_list):
                if i > 0:
                    trace_list = _plotplotly_iterate(trajectory, trace_list=[], included_species_list= included_species_list,
                                                     show_labels=False)
                else:
                    trace_list = _plotplotly_iterate(trajectory, trace_list=[], included_species_list=included_species_list)

                for k in range(0,len(trace_list)):
                    if i%2 == 0:
                        fig.append_trace(trace_list[k], int(i/2) + 1, 1)
                    else:
                        fig.append_trace(trace_list[k], int(i/2) + 1, 2)

                fig['layout'].update(autosize=True,
                                     height=400*len(trajectory_list),
                                     showlegend=show_legend,title =title)

            

        else:
            trace_list = []
            for i,trajectory in enumerate(trajectory_list):
                if i > 0:
                    trace_list = _plotplotly_iterate(trajectory, trace_list=trace_list,included_species_list= included_species_list,
                                                     show_labels = False)
                else:
                    trace_list = _plotplotly_iterate(trajectory, trace_list=trace_list,included_species_list= included_species_list)

            layout = go.Layout(
                showlegend=show_legend,
                title=title,
                xaxis=dict(
                    title=xaxis_label),
                yaxis=dict(
                    title=yaxis_label)
            )

            fig['data'] = trace_list
            fig['layout'] = layout

        if return_plotly_figure:
            return fig
        else:
            iplot(fig)


    def average_ensemble(self):
        """
                Generate a single Results object with a Trajectory that is made of the means of all trajectories' outputs
                :return: the Results object
                """

        trajectory_list = self.data
        number_of_trajectories = len(trajectory_list)

        output_trajectory = Trajectory(data={},model=trajectory_list[0].model,solver_name=trajectory_list[0].solver_name)

        for species in trajectory_list[0]: #Initialize the output to be the same size as the inputs
            output_trajectory[species] = [0]*len(trajectory_list[0][species])

        output_trajectory['time'] = trajectory_list[0]['time']

        for i in range(0,number_of_trajectories): #Add every value of every Trajectory Dict into one output Trajectory
            trajectory_dict = trajectory_list[i]
            for species in trajectory_dict:
                if species == 'time':
                    continue
                for k in range(0,len(output_trajectory[species])):
                    output_trajectory[species][k] += trajectory_dict[species][k]

        for species in output_trajectory:   #Divide for mean of every value in output Trajectory
            if species == 'time':
                continue
            for i in range(0,len(output_trajectory[species])):
                output_trajectory[species][i] /= number_of_trajectories

        output_results = Results(data=[output_trajectory]) #package output_trajectory in a Results object

        return output_results

    def stddev_ensemble(self,ddof = 0):
        """
                Generate a single Results object with a Trajectory that is made of the sample standard deviations of all 
                trajectories' outputs.

                  Attributes
                ----------
                ddof : int
                    Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents
                    the number of trajectories. Sample standard deviation uses ddof of 1. Defaults to population
                    standard deviation where ddof is 0.

                :return: the Results object
                """

        from math import sqrt

        trajectory_list = self.data
        number_of_trajectories = len(trajectory_list)

        if ddof == number_of_trajectories:
            warnings.warn("ddof must be less than the number of trajectories. Using ddof of 0")
            ddof = 0

        average_list = self.average_ensemble().data[0]

        output_trajectory = Trajectory(data={}, model=trajectory_list[0].model, solver_name=trajectory_list[0].solver_name)

        for species in trajectory_list[0]: #Initialize the output to be the same size as the inputs
            output_trajectory[species] = [0]*len(trajectory_list[0][species])

        output_trajectory['time'] = trajectory_list[0]['time']

        for i in range(0,number_of_trajectories):
            trajectory_dict = trajectory_list[i]
            for species in trajectory_dict:
                if species == 'time':
                    continue
                for k in range(0,len(output_trajectory['time'])):
                    output_trajectory[species][k] += (trajectory_dict[species][k] - average_list[species][k])\
                                          *(trajectory_dict[species][k] - average_list[species][k])

        for species in output_trajectory:   #Divide for mean of every value in output Trajectory
            if species == 'time':
                continue
            for i in range(0,len(output_trajectory[species])):
                output_trajectory[species][i] /= (number_of_trajectories - ddof)
                output_trajectory[species][i] = sqrt(output_trajectory[species][i])

        output_results = Results(data=[output_trajectory]) #package output_trajectory in a Results object
        return output_results

    def plotplotly_std_dev_range(self, xaxis_label = "Time (s)", yaxis_label="Species Population", title = None,
                                 show_legend=True, included_species_list = [],return_plotly_figure=False,ddof = 0):
        """
           Plot a plotly graph depicting standard deviation and the mean graph of a results object

         Attributes
        ----------
        xaxis_label : str
            the label for the x-axis
        yaxis_label : str
            the label for the y-axis
        title : str
            the title of the graph
        show_legend : bool
            whether or not to display a legend which lists species
        included_species_list : list
            A list of strings describing which species to include. By default displays all species.
        return_plotly_figure : bool
            whether or not to return a figure dictionary of data(graph object traces) and layout options
            which may be edited by the user.
        ddof : int
            Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents
            the number of trajectories. Sample standard deviation uses ddof of 1. Defaults to population
            standard deviation where ddof is 0.
        **plotly_args: dict
            Optional additional arguments to be passed to plotly's Layout constructor.

        """

        average_trajectory = self.average_ensemble().data[0]
        stddev_trajectory = self.stddev_ensemble(ddof= ddof).data[0]

        from plotly.offline import init_notebook_mode, iplot
        import plotly.graph_objs as go

        init_notebook_mode(connected=True)

        if title is None:
            title = (self._validate_title() + " - Standard Deviation Range")

        trace_list=[]
        for species in average_trajectory:
            if species != 'time':

                if species not in included_species_list and included_species_list:
                    continue

                upper_bound = []
                for i in range(0, len(average_trajectory[species])):
                    upper_bound.append(average_trajectory[species][i] + stddev_trajectory[species][i])

                trace_list.append(
                    go.Scatter(
                        name=species+ ' Upper Bound',
                        x=average_trajectory['time'],
                        y = upper_bound,
                        mode='lines',
                        marker=dict(color="#444"),
                        line=dict(width=1,dash='dot'),
                        legendgroup="Standard Deviation",
                        showlegend=False
                    )
                )
                trace_list.append(
                    go.Scatter(
                        x=average_trajectory['time'],
                        y=average_trajectory[species],
                        name=species,
                        fillcolor='rgba(68, 68, 68, 0.2)',
                        fill='tonexty'
                    )
                )

                lower_bound = []
                for i in range(0, len(average_trajectory[species])):
                    lower_bound.append(average_trajectory[species][i] - stddev_trajectory[species][i])

                trace_list.append(
                    go.Scatter(
                        name=species + ' Lower Bound',
                        x=average_trajectory['time'],
                        y= lower_bound,
                        mode='lines',
                        marker=dict(color="#444"),
                        line=dict(width=1,dash='dot'),
                        fillcolor='rgba(68, 68, 68, 0.2)',
                        fill='tonexty',
                        legendgroup="Standard Deviation",
                        showlegend=False
                    )
                )
        layout = go.Layout(
            showlegend=show_legend,
            title=title,
            xaxis=dict(
                title=xaxis_label),
            yaxis=dict(
                title=yaxis_label)
        )
        fig = dict(data=trace_list, layout=layout)

        if return_plotly_figure:
            return fig
        else:
            iplot(fig)

    def plot_std_dev_range(self, xaxis_label ="Time (s)", yaxis_label ="Species Population", title = None,
                           style="default", show_legend=True, included_species_list=[],ddof=0,save_png = False,figsize = (18,10)):
        """
            Plot a matplotlib graph depicting standard deviation and the mean graph of a results object

         Attributes
        ----------
        xaxis_label : str
            the label for the x-axis
        yaxis_label : str
            the label for the y-axis
        title : str
            the title of the graph
        show_legend : bool
            whether or not to display a legend which lists species
        included_species_list : list
            A list of strings describing which species to include. By default displays all species.
        ddof : int
            Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents
            the number of trajectories. Sample standard deviation uses ddof of 1. Defaults to population
            standard deviation where ddof is 0.
        save_png : bool or str
            Should the graph be saved as a png file. If True, File name is title of graph. If a string is given, file
            is named after that string.
        figsize : tuple
            the size of the graph. A tuple of the form (width,height). Is (18,10) by default.

        """

        average_result = self.average_ensemble().data[0]
        stddev_trajectory = self.stddev_ensemble(ddof=ddof).data[0]

        import matplotlib.pyplot as plt

        try:
            plt.style.use(style)
        except:
            warnings.warn("Invalid matplotlib style. Try using one of the following {}".format(plt.style.available))
            plt.style.use("default")

        plt.figure(figsize=figsize)

        for species in average_result:
            if species == 'time':
                continue

            if species not in included_species_list and included_species_list:
                continue

            lowerBound = [a-b for a,b in zip(average_result[species], stddev_trajectory[species])]
            upperBound = [a+b for a,b in zip(average_result[species], stddev_trajectory[species])]

            plt.fill_between(average_result['time'], lowerBound, upperBound,color='whitesmoke')
            plt.plot(average_result['time'],lowerBound,upperBound,color='grey',linestyle='dashed')
            plt.plot(average_result['time'],average_result[species],label=species)

        if title is None:
            title = (self._validate_title() + " - Standard Deviation Range")

        plt.title(title, fontsize=18)
        plt.xlabel(xaxis_label)
        plt.ylabel(yaxis_label)
        plt.plot([0], [11])
        if show_legend:
            plt.legend(loc='best')

        if isinstance(save_png, str):
            plt.savefig(save_png)

        elif save_png:
            plt.savefig(title)

        
