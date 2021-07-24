#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 24 17:29:44 2021

@author: mattwear
"""

### Pose Analysis Functions

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
import math
import cv2

mpii_edges = [[0, 1], [1, 2], [2, 6], [6, 3], [3, 4], [4, 5], 
              [10, 11], [11, 12], [12, 8], [8, 13], [13, 14], [14, 15], 
              [6, 8], [8, 9]]

def plot3D(ax, points, edges, marker_size = 100):
    ax.grid(False)
    oo = 1e10
    xmax,ymax,zmax = -oo,-oo,-oo
    xmin,ymin,zmin = oo, oo, oo
    #edges = mpii_edges
    c='b'
    marker = 'o'
    points = points.reshape(-1, 3)
    x, y, z = np.zeros((3, points.shape[0]))
    for j in range(points.shape[0]):
        x[j] = points[j, 0].copy()
        y[j] = points[j, 2].copy()
        z[j] = -points[j, 1].copy()
        xmax = max(x[j], xmax)
        ymax = max(y[j], ymax)
        zmax = max(z[j], zmax)
        xmin = min(x[j], xmin)
        ymin = min(y[j], ymin)
        zmin = min(z[j], zmin)
    ax.scatter(x, y, z, s = marker_size, c = c, marker = marker)
    for e in edges:
        ax.plot(x[e], y[e], z[e], c = c)
    max_range = np.array([xmax-xmin, ymax-ymin, zmax-zmin]).max()
    Xb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(xmax+xmin)
    Yb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(ymax+ymin)
    Zb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(zmax+zmin)
    for xb, yb, zb in zip(Xb, Yb, Zb):
        ax.plot([xb], [yb], [zb], 'w')
        
#2D plot of the 3D body pose in the x-y plane (ignoring z-axis)
def plot2D(ax, pose_3d, mpii_edges):
    for e in range(len(mpii_edges)):
        ax.plot(pose_3d[mpii_edges[e]][:, 0], -1*pose_3d[mpii_edges[e]][:, 1])

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    
def plot2D3DPose(array_id, save_df, poses_2d, poses_3d, img_path, mpii_edges):
    img_file = save_df['file'][array_id]
    image = importImage(img_path + img_file)
    pose_2d = pose_to_matrix(poses_2d[array_id])
    pose_3d = pose_to_matrix(poses_3d[array_id])
    print('Array ID: ' + str(array_id))
    print("File Name: " + img_file)

    fig = plt.figure(figsize=(8, 6))
    #fig.patch.set_visible(False)
    ax = fig.add_subplot(2, 2, 1)
    ax.imshow(image)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.axis('off')
    ax.set_title('(a) Input Image', y=-0.14)

    ax = fig.add_subplot(2, 2, 2)
    ax.imshow(image)
    for e in range(len(mpii_edges)):
        ax.plot(pose_2d[mpii_edges[e]][:, 0], pose_2d[mpii_edges[e]][:, 1], c='b', lw=3, marker='o')
    ax.set_yticks([])
    ax.set_xticks([])
    ax.axis('off')
    ax.set_title('(b) 2D Pose Estimation', y=-0.14)

    ax = fig.add_subplot(2, 2, 3, projection='3d')
    plot3D(ax, pose_3d, mpii_edges, marker_size=30)
    ax.set_title('(c) 3D Pose Estimation (CVI)', y=-0.23)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_zticks([])
    
    ax = fig.add_subplot(2, 2, 4)
    plot2D(ax, pose_3d, mpii_edges)
    ax.set_title('(d) 3D Pose Estimation (CVI) 2D Projection', y=-0.2)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    plt.tight_layout()
    #plt.savefig('viz/poseEstimationExample.png', dpi=500)
    plt.show()
        
def pose_to_matrix(pose):
    if len(pose) == 48:
        pose_matrix = pose.reshape(16, 3)
    else:
        pose_matrix = pose.reshape(16, 2)
    return pose_matrix

def importImage(img):
    #Import image
    image = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)
    return image

def rotatePose(pose_3d, theta):
    #Rotate body pose by theta degrees around the y axis
    #Input: pose_3d - 16x3 array representing the coordinates of the body pose
    #Returns: 16x3 array of rotated body pose coordinates
    radian = math.radians(theta)

    rotation_matrix = np.array([[np.cos(radian), 0, np.sin(radian)],
                                [0, 1, 0],
                                [-np.sin(radian), 0, np.cos(radian)]])

    rotated_pose = np.zeros((len(pose_3d), 3))
    for i in range(len(pose_3d)):
        rotated_pose[i] = rotation_matrix @ pose_3d[i]
    return rotated_pose

def hipWidth(pose_3d):
    #Input: pose_3d - 16x3 np array representing a single 3D body pose
    #Returns euclidean distance in x-y space of the two hip joints
    #Indices of both hip locations are 2 and 3.
    return np.linalg.norm(pose_3d[3][:2]-pose_3d[2][:2])

def cameraInvariantPose(pose_3d):
    # Function to get the optimal rotated pose
    best_pose = pose_3d
    max_hip_width = hipWidth(pose_3d)
    theta_ranges = list(range(10, 100, 10)) + list(range(270, 360, 10))

    for theta in theta_ranges:
        rotated_pose = rotatePose(pose_3d, theta=theta)
        hip_width = hipWidth(rotated_pose)
        if hip_width > max_hip_width:
            best_pose = rotated_pose
            max_hip_width = hip_width
    return best_pose

def cameraInvariantDataset(raw_poses):
    #Converts the raw body point dataset to a cleaned camera-invariant one
    cleaned_pose_arr = raw_poses.copy()
    for i in range(len(raw_poses)):
        pose_3d = pose_to_matrix(raw_poses[i])
        best_pose = cameraInvariantPose(pose_3d)
        cleaned_pose_arr[i] = best_pose.flatten()
    return cleaned_pose_arr


