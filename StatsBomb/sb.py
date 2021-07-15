#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 23:13:57 2021

@author: mattwear
"""

import numpy as np
import json
#from pandas.io.json import json_normalize
import pandas as pd
from os import listdir
import matplotlib.pyplot as plt

def importSBjson(file_name, path='data/events/'):
    with open(path+file_name) as data_file:
        #print (mypath+'events/'+file)
        data = json.load(data_file)
    
    #get the nested structure into a dataframe 
    #store the dataframe in a dictionary with the match id as key (remove '.json' from string)
    df = pd.json_normalize(data, sep = "_").assign(match_id = file_name[:-5])
    return df


events = importSBjson(file_name='14304.json')

def getPensFromMatch(events):
    #Get penalties from event data, keeping only useful columns
    pens = events.loc[events['shot_type_name'] == 'Penalty'].set_index('id')
    keep_cols = ['match_id','minute','team_id','team_name','player_id','player_name',
             'shot_body_part_name','shot_technique_name','shot_outcome_name']
    return pens[keep_cols]

pens = getPensFromMatch(events)

def getPensFromDir(path='data/events/'):
    pens_df = pd.DataFrame()
    files = listdir(path)
    i = 1
    num_files = len(files)
    for file in files:
        events = importSBjson(file_name=file)
        pens = getPensFromMatch(events)
        if pens.shape[0] > 0:
            pens_df = pd.concat([pens_df, pens])
            
        print('Done ' + str(i) + ' of ' + str(num_files) + ' files')
        i += 1
    return pens_df

pens_df = getPensFromDir(path='data/events/')

def getMatches():
    #Open match datasets
    with open('data/matches/2/'+'1.json') as data_file:
            #print (mypath+'events/'+file)
            season1 = json.load(data_file)
            
    with open('data/matches/2/'+'4.json') as data_file:
            #print (mypath+'events/'+file)
            season2 = json.load(data_file)
            
    matches = season1 + season2
    return matches

matches = getMatches()

def mergeMatchesAndPenData(pens_df, matches):
    match_info_df = pd.DataFrame()
    m_ids = np.unique(pens_df.match_id).astype(int)
    
    for m_id in m_ids:
        #Find particular match
        filter_matches = [x for x in matches if x['match_id'] == m_id]
        
        date = filter_matches[0]['match_date']
        h_team = filter_matches[0]['home_team']['home_team_name']
        a_team = filter_matches[0]['away_team']['away_team_name']
        season = filter_matches[0]['season']['season_name']
        comp = filter_matches[0]['competition']['competition_name']
        
        to_append = pd.Series([m_id, date, h_team, a_team, season, comp])
        
        match_info_df = match_info_df.append(to_append, ignore_index=True)
        
    match_info_df.columns = ['match_id','date','home_team',
                             'away_team','season','competition']
    pens_df.match_id = pens_df.match_id.astype(int)
    match_info_df.match_id = match_info_df.match_id.astype(int)
    
    #Merge pens_df and match_info_df by match_id
    pens_df = pens_df.merge(match_info_df, how='left', on='match_id')
    return pens_df

pens_df = mergeMatchesAndPenData(pens_df, matches)

def addGKInfo(pens_df):
    pens_df['gk_id'] = np.nan
    pens_df['gk_name'] = np.nan
    #Input match_id, team_id of shooter, minute of pen
    for i in range(len(pens_df)):
        m_id = pens_df['match_id'][i]
        t_id = pens_df['team_id'][i]
        events = importSBjson(file_name=str(m_id)+'.json')
        players = events[(events.type_id == 35) & (events.team_id != t_id)].reset_index()['tactics_lineup'][0]
        gk = [x for x in players if x['position']['name']=='Goalkeeper']
        gk_id = gk[0]['player']['id']
        gk_name = gk[0]['player']['name']
        pens_df.loc[i, 'gk_id'] = gk_id
        pens_df.loc[i, 'gk_name'] = gk_name
        print(i)
    return pens_df

pens_df = addGKInfo(pens_df)
pens_df.player_id = pens_df.player_id.astype(int)
pens_df.gk_id = pens_df.gk_id.astype(int)

pens_df.to_csv('prem_pens_df.csv')


#### One v Ones
# World Cup

def importSBMatches(file_name, path='data/matches/2/'):
    with open(path+file_name) as data_file:
        #print (mypath+'events/'+file)
        data = json.load(data_file)
    
    #get the nested structure into a dataframe 
    #store the dataframe in a dictionary with the match id as key (remove '.json' from string)
    df = pd.json_normalize(data, sep = "_")
    return df

def getShots(events):
    #Get penalties from event data, keeping only useful columns
    shots = events.loc[events['type_name'] == 'Shot'].set_index('id')
    keep_cols = ['match_id','minute','team_id','team_name','player_id','player_name',
             'shot_body_part_name','shot_technique_name','shot_outcome_name']
    return pens[keep_cols]

matches_wc = importSBMatches('3.json', path='open-data/data/matches/43/')
match_ids = matches_wc.match_id

#Get all shots in the World Cup
wc_shots = pd.DataFrame()
for m_id in match_ids:
    file_name = str(m_id) + '.json'
    events = importSBjson(file_name, path='open-data/data/events/')
    shots = events.loc[events['type_name'] == 'Shot']
    wc_shots = wc_shots.append(shots, ignore_index=True)

#Filter for shots with feet that are also from open play
onevone = wc_shots[(wc_shots['shot_body_part_name'] == 'Right Foot') | (wc_shots['shot_body_part_name'] == 'Left Foot')].copy()
onevone = onevone[onevone['shot_type_name'] == 'Open Play'].copy()
keep_columns = ['timestamp','duration','play_pattern_name','team_name','location',
                'player_id','player_name','under_pressure','shot_end_location',
                'shot_outcome_name','shot_body_part_name','shot_technique_name',
                'shot_freeze_frame','shot_first_time','match_id']
onevone = onevone[keep_columns].copy().reset_index(drop=True)

#Filter for 1v1s
shot_id = 0
#onevone['shot_freeze_frame'][shot_id][0]['position']['name']
shooter_x = onevone['location'][shot_id][0]
shooter_y = onevone['location'][shot_id][1]

is_gk = []
freeze_frame_x = []
freeze_frame_y = []
for i in range(len(onevone['shot_freeze_frame'][shot_id])):
    freeze_frame_x.append(onevone['shot_freeze_frame'][shot_id][i]['location'][0])
    freeze_frame_y.append(onevone['shot_freeze_frame'][shot_id][i]['location'][1])
    is_gk.append(onevone['shot_freeze_frame'][shot_id][i]['position']['name'] == 'Goalkeeper')

pitchLengthX=120
pitchWidthY=80
from FCPython import createPitch
from FCPython import createGoalMouth
(fig,ax) = createPitch(pitchLengthX,pitchWidthY,'yards','gray')
#(fig,ax) = createGoalMouth()

plt.scatter(freeze_frame_x, freeze_frame_y, c=is_gk, s=4)
plt.scatter(shooter_x, shooter_y, c='b', s=4)
plt.show()







