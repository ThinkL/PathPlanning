"""
This is fast marching tree* code for 3D
@author: yue qi 
source: Janson, Lucas, et al. "Fast marching tree: A fast marching sampling-based method 
        for optimal motion planning in many dimensions." 
        The International journal of robotics research 34.7 (2015): 883-921.
"""
import numpy as np
import matplotlib.pyplot as plt
import time
import copy


import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../Sampling_based_Planning/")
from rrt_3D.env3D import env
from rrt_3D.utils3D import getDist, sampleFree, nearest, steer, isCollide
from rrt_3D.plot_util3D import make_get_proj, draw_block_list, draw_Spheres, draw_obb, draw_line, make_transparent
from rrt_3D.queue import MinheapPQ

class FMT_star:

    def __init__(self):
        self.env = env()
        # init start and goal
            # note that the xgoal could be a region since this algorithm is a multiquery method
        self.xinit, self.xgoal = tuple(self.env.start), tuple(self.env.goal)
        self.x0, self.xt = tuple(self.env.start), tuple(self.env.goal) # used for sample free
        self.n = 1000 # number of samples
        self.radius = 2.5 # radius of the ball
        # sets
        self.Vopen, self.Vopen_queue, self.Vclosed, self.V, self.Vunvisited, self.c = self.initNodeSets()
        # make space for save 
        self.neighbors = {}
        # additional
        self.done = True
        self.Path = []

    def generateSampleSet(self, n):
        V = set()
        for i in range(n):
            V.add(tuple(sampleFree(self, bias = 0.0)))
        return V

    def initNodeSets(self):
        # open set
        Vopen = {self.xinit} # open set
        # closed set
        closed = set()
        # V, Vunvisited set 
        V = self.generateSampleSet(self.n - 2) # set of all nodes
        Vunvisited = copy.deepcopy(V) # unvisited set
        Vunvisited.add(self.xgoal)
        V.add(self.xinit)
        V.add(self.xgoal)
        # initialize all cost to come at inf
        c = {node : np.inf for node in V}
        c[self.xinit] = 0
        # use a min heap to speed up
        Vopen_queue = MinheapPQ()
        Vopen_queue.put(self.xinit, c[self.xinit]) # priority organized as the cost to come
        return Vopen, Vopen_queue, closed, V, Vunvisited, c

    def Near(self, nodeset, node, rn):
        if node in self.neighbors:
            return self.neighbors[node]
        validnodes = {i for i in nodeset if getDist(i, node) < rn}
        return validnodes

    def Save(self, V_associated, node):
        self.neighbors[node] = V_associated

    def path(self, z, T):
        V, E = T
        path = []
        return path

    def Cost(self, x, y):
        # collide, dist = isCollide(self, x, y)
        # if collide:
        #     return np.inf
        # return dist
        return getDist(x, y)

    def FMTrun(self):
        z = self.xinit
        rn = self.radius
        Nz = self.Near(self.Vunvisited, z, rn)
        E = set()
        self.Save(Nz, z)
        ind = 0
        while z != self.xgoal:
            Vopen_new = set()
            Nz = self.Near(self.Vunvisited, z, rn)
            Xnear = Nz.intersection(self.Vunvisited)
            for x in Xnear:
                Nx = self.Near(self.V.difference({x}), x, rn)
                self.Save(Nx, x)
                Ynear = list(Nx.intersection(self.Vopen))
                ymin = Ynear[np.argmin([self.c[y] + self.Cost(y,x) for y in Ynear])] # DP programming equation
                collide, _ = isCollide(self, ymin, x)
                if not collide:
                    E.add((ymin, x)) # straight line joining ymin and x is collision free
                    Vopen_new.add(x)
                    self.Vunvisited = self.Vunvisited.difference({x})
                    self.c[x] = self.c[ymin] + self.Cost(ymin, x) # estimated cost-to-arrive from xinit in tree T = (VopenUVclosed, E)
            # update open set
            print(len(self.Vopen))
            self.Vopen = self.Vopen.union(Vopen_new).difference({z})
            self.Vclosed.add(z)
            if len(self.Vopen) == 0:
                print('Failure')
                return 
            ind += 1
            self.visualization(ind, E)
            # update current node
            Vopenlist = list(self.Vopen)
            z = Vopenlist[np.argmin([self.c[y] for y in self.Vopen])]
        # creating the tree
        T = (self.Vopen.union(self.Vclosed), E)
        return self.path(z, T)

    def visualization(self, ind, E):
        if ind % 100 == 0 or self.done:
            #----------- list structure
            # V = np.array(list(initparams.V))
            # E = initparams.E
            #----------- end
            # edges = initparams.E
            Path = np.array(self.Path)
            start = self.env.start
            goal = self.env.goal
            # edges = E.get_edge()
            #----------- list structure
            edges = np.array(list(E))
            #----------- end
            # generate axis objects
            ax = plt.subplot(111, projection='3d')
            
            # ax.view_init(elev=0.+ 0.03*initparams.ind/(2*np.pi), azim=90 + 0.03*initparams.ind/(2*np.pi))
            # ax.view_init(elev=0., azim=90.)
            ax.view_init(elev=8., azim=90.)
            # ax.view_init(elev=-8., azim=180)
            ax.clear()
            # drawing objects
            draw_Spheres(ax, self.env.balls)
            draw_block_list(ax, self.env.blocks)
            if self.env.OBB is not None:
                draw_obb(ax, self.env.OBB)
            draw_block_list(ax, np.array([self.env.boundary]), alpha=0)
            draw_line(ax, edges, visibility=0.75, color='g')
            draw_line(ax, Path, color='r')
            # if len(V) > 0:
            #     ax.scatter3D(V[:, 0], V[:, 1], V[:, 2], s=2, color='g', )
            ax.plot(start[0:1], start[1:2], start[2:], 'go', markersize=7, markeredgecolor='k')
            ax.plot(goal[0:1], goal[1:2], goal[2:], 'ro', markersize=7, markeredgecolor='k')
            # adjust the aspect ratio
            xmin, xmax = self.env.boundary[0], self.env.boundary[3]
            ymin, ymax = self.env.boundary[1], self.env.boundary[4]
            zmin, zmax = self.env.boundary[2], self.env.boundary[5]
            dx, dy, dz = xmax - xmin, ymax - ymin, zmax - zmin
            ax.get_proj = make_get_proj(ax, 1 * dx, 1 * dy, 2 * dy)
            make_transparent(ax)
            #plt.xlabel('x')
            #plt.ylabel('y')
            ax.set_axis_off()
            plt.pause(0.0001)

if __name__ == '__main__':
    A = FMT_star()
    A.FMTrun()


