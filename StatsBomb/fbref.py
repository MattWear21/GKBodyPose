#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 13:44:40 2021

@author: mattwear
"""

###Used to find out the games in 2020-21 and 2019-20 in which a pen was taken

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import numpy as np


def getMatchURLs():
    #Find all match URLs for every game in the 2020-21 PL season
    urls = ['https://fbref.com/en/comps/9/3232/schedule/2019-2020-Premier-League-Scores-and-Fixtures',
            'https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures']
    
    match_urls = []
    
    for url in urls:
        res = requests.get(url)
        ## The next two lines get around the issue with comments breaking the parsing.
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("",res.text),'lxml')
        all_tables = soup.findAll("tbody")
        match_table = all_tables[0]
        
        rows_match = match_table.find_all('tr')
        
        for row in rows_match:
            cell = row.find("td",{"data-stat": 'match_report'})
            match_link = cell.findAll("a", href=True)
            if len(match_link) > 0:
                to_append = match_link[0]['href']
                match_urls.append(to_append)
    
    return match_urls

match_urls = getMatchURLs()


def getPens(match_url):
    #Get all pens
    fbref_pens_df = pd.DataFrame()
    
    url = 'https://fbref.com' + match_url
    res = requests.get(url)
    ## The next two lines get around the issue with comments breaking the parsing.
    comm = re.compile("<!--|-->")
    soup = BeautifulSoup(comm.sub("",res.text),'lxml')
    all_tables = soup.findAll("tbody")
    
    for i in [0, 7]:
        
        name_list = []
        pens_att_list = []
        pens_made_list = []
        position_list = []
    
        player_table = all_tables[i]
        rows_player = player_table.find_all('tr')
        
        for row in rows_player:
            #Get player name and number of pens attempted and scored
            cell_player = row.find("th", {'data-stat': 'player'})
            a = cell_player.text.strip().encode()
            name_list.append(a.decode("utf-8"))
            
            cell = row.find("td",{"data-stat": 'pens_att'})
            a = cell.text.strip().encode()
            pens_att_list.append(int(a.decode("utf-8")))
            
            cell = row.find("td",{"data-stat": 'pens_made'})
            a = cell.text.strip().encode()
            pens_made_list.append(int(a.decode("utf-8")))
            
            cell = row.find("td",{"data-stat": 'position'})
            a = cell.text.strip().encode()
            position_list.append(a.decode("utf-8"))
        
        name_list = np.array(name_list)
        pens_att_list = np.array(pens_att_list)
        pens_made_list = np.array(pens_made_list)
        position_list = np.array(position_list)
        
        #Find home and away goalkeers
        if i == 0:
            home_goalkeepers = ",".join(name_list[position_list == 'GK'])
            home_players = name_list
        else:
            away_goalkeepers = ",".join(name_list[position_list == 'GK'])
            away_players = name_list
        
        names = name_list[pens_att_list > 0]
        pens_made = pens_made_list[pens_att_list > 0]
        pens_att = pens_att_list[pens_att_list > 0]
        
        num_pens_att = np.sum(pens_att_list)
        #print(num_pens_att)
        
        #Dataframe of pens for a match: match_url, pen_taker, scored/missed
        match_pens_df = pd.DataFrame()
        
        if num_pens_att > 0:
            links_df = np.repeat(match_url, num_pens_att)
            
            names_df = np.repeat(names, pens_att)
                
            success_df = np.array([])
            for n in range(len(names)):
                #total_attempts = pens_att[n]
                scored = np.repeat('Scored', pens_made[n])
                missed = np.repeat('Missed', pens_att[n] - pens_made[n])
                player_success = np.concatenate((scored,missed), axis=None)
                success_df = np.concatenate((success_df, player_success))
                
                
            match_pens_df['url'] = links_df
            match_pens_df['pen_taker'] = names_df
            match_pens_df['outcome'] = success_df
        
        fbref_pens_df = pd.concat([fbref_pens_df, match_pens_df])
    
    fbref_pens_df = fbref_pens_df.reset_index(drop=True)
    
    fbref_pens_df['goalkeepers'] = np.nan
    for i in range(len(fbref_pens_df)):
        if fbref_pens_df.loc[i, 'pen_taker'] in home_players:
            fbref_pens_df.loc[i, 'goalkeepers'] = away_goalkeepers
        else:
            fbref_pens_df.loc[i, 'goalkeepers'] = home_goalkeepers
            
    #print(fbref_pens_df)
    return fbref_pens_df
    

match_url = match_urls[299]
test = getPens(match_url)


all_pens_df = pd.DataFrame()
i = 0

for url in match_urls[299:]:
    pens = getPens(url)
    all_pens_df = pd.concat([all_pens_df, pens])
    print(str(i) + ' / ' + str(len(match_urls)))
    i += 1
    
all_pens_df = all_pens_df.reset_index(drop=True)
all_pens_df.to_csv('prem_pens_192021_df.csv')
#all_pens_df = getAllPens(match_urls)




