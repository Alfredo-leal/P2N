# -*- coding: utf-8 -*-
"""
Created on Tue Avr 1 13:41:21 2014

@author: dreymond
"""
import networkx as nx
#import copy

#dicot = copy.deepcopy(dict)

import os
import datetime
import pydot
import ctypes # pydot needed for pyinstaller !!! seems that ctype also I should learn making hooks....
from urllib import quote as quot
import numpy as np
import matplotlib.cm
#from networkx_functs import calculate_degree, calculate_betweenness, calculate_degree_centrality
import cPickle as pickle
import copy
from P2N_Lib import ReturnBoolean, LoadBiblioFile, UrlPatent,UrlApplicantBuild,UrlInventorBuild,UrlIPCRBuild, cmap_discretize, flatten, DecoupeOnTheFly
#from P2N_Lib import getStatus2, getClassif,getCitations, getFamilyLenght, isMaj, quote, GenereDateLiens
#from P2N_Lib import  symbole, ReturnBoolean, FormateGephi, GenereListeSansDate, GenereReseaux3, cmap_discretize
#from Ops3 import UnNest2List


DureeBrevet = 20
SchemeVersion = '20140101' #for the url to the classification scheme

Networks =dict()
#next lines are here to avoid the changing scheme lecture of requete.cql
Networks["_CountryCrossTech"] =  [False, [ 'IPCR7', "country"]]
Networks["_CrossTech"] =  [False, ['IPCR7']]
Networks["_InventorsCrossTech"] =  [False, ['IPCR7', "inventor-nice"]]
Networks["_Applicants_CrossTech"] =  [False, ['IPCR7', "applicant-nice"]]
Networks["_ApplicantInventor"] = [False, ["applicant-nice", "inventor-nice"]]
Networks["_Applicants"] =  [False, ["applicant-nice"]]
Networks["_Inventors"] =  [False, ["inventor-nice"]]

Networks["_References"] =  [True, [ 'label', 'CitP', "CitO"]]
Networks["_Citations"] =  [True, [ 'label', "CitedBy"]]
Networks["_Equivalents"] =  [True, [ 'label', "equivalents"]]
#here we start
Networks["_FamiliesNetwork"] =  [True, [ "equivalents", u'family lenght', "applicant-nice", 'IPCR7', 'representative', 'prior']]


ListeBrevet = []
#ouverture fichier de travail
#On récupère la requête et les noms des fichiers de travail
with open("..//requete.cql", "r") as fic:
    contenu = fic.readlines()
    for lig in contenu:
        #if not lig.startswith('#'):
            if lig.count('request:')>0:
                requete=lig.split(':')[1].strip()
            if lig.count('DataDirectory:')>0:
                ndf = lig.split(':')[1].strip()
            if lig.count('GatherContent')>0:
                Gather = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('GatherBiblio')>0:
                GatherBiblio = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('GatherPatent')>0:
                GatherPatent = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('GatherFamilly')>0:
                GatherFamilly = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('InventorNetwork')>0:
                Networks["_Inventors"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('ApplicantNetwork')>0:
                Networks["_Applicants"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('ApplicantInventorNetwork')>0:
                Networks["_ApplicantInventor"] [0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('InventorCrossTechNetwork')>0:
                Networks["_InventorsCrossTech"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('ApplicantCrossTechNetwork')>0:
                Networks["_Applicants_CrossTech"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('CountryCrossTechNetwork')>0:
                Networks["_CountryCrossTech"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('CrossTechNetwork')>0:
                Networks["_CrossTech"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('CompleteNetwork')>0:
                P2NComp = ReturnBoolean(lig.split(':')[1].strip())    
            if lig.count('FamiliesNetwork')>0:
                P2NFamilly = ReturnBoolean(lig.split(':')[1].strip())    
            if lig.count('FamiliesHierarchicNetwork')>0:
                P2NHieracFamilly = ReturnBoolean(lig.split(':')[1].strip())    
            if lig.count('References')>0:
                Networks["_References"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('Citations')>0:
                Networks["_Citations"][0] = ReturnBoolean(lig.split(':')[1].strip())
            if lig.count('Equivalents')>0:
                Networks["_Equivalents"][0] = ReturnBoolean(lig.split(':')[1].strip())


BiblioPath = '..//DATA//'+ndf+'//PatentBiblios'
temporPath = '..//DATA//'+ndf+'//tempo'


NeededInfo = ['label', 'date', 'prior-dateDate']
#overloading toi False network creation, these are processed through p2n-NetworkMix script
Networks["_CountryCrossTech"] =  [False, [ 'IPCR7', "country"]]
Networks["_CrossTech"] =  [False, ['IPCR7']]
Networks["_InventorsCrossTech"] =  [False, ['IPCR7', "inventor-nice"]]
Networks["_Applicants_CrossTech"] =  [False, ['IPCR7', "applicant-nice"]]
Networks["_ApplicantInventor"] = [False, ["applicant-nice", "inventor-nice"]]
Networks["_Applicants"] =  [False, ["applicant-nice"]]
Networks["_Inventors"] =  [False, ["inventor-nice"]]
Networks["_References"] =  [False, [ 'label', 'CitP', "CitO"]]
Networks["_Citations"] =  [False, [ 'label', "CitedBy"]]
Networks["_Equivalents"] =  [False, [ 'label', "equivalents"]]
Networks["_FamiliesNetwork"] =  [True, [ "equivalents", u'family lenght', "applicant-nice", 'IPCR7', 'representative', 'prior']]
Category =dict()
Prior = dict()
Poids=dict()
appars = []
somme =  0
network = "_FamiliesNetwork"
mixNet = Networks[network][1]
if Networks[network][0]:
    ListeBrevet =[]         # patentList
    Patents = set()         # Patents labels
    Nodes = dict()   # Nodes of the Graph
    Appariement = [] # collaborations for each patent
    dateMini = datetime.date(3000,1,1)
    dateMaxi =  datetime.date(1000,1,1)
    NeededInfo .extend(mixNet)  # list of needed field for building the net
    # may be should use  from
 #from collections import OrderedDict
 #class OrderedNodeGraph(nx.Graph):
  #   node_dict_factory=OrderedDict
 # G = OrderedNodeGraph()
    G1 = nx.DiGraph()        # dynamic network for Gephi 
    attr_dict = dict()       # attributes for the net
           # flat net for gexf.js may be it is possible to use previous instead of this one...
    
    if 'Description'+ndf in os.listdir(BiblioPath):    
        DataBrevet = LoadBiblioFile(BiblioPath, 'Families'+ ndf)
    print "bibliographic data of Families", ndf, " patent universe found: ", len(DataBrevet["brevets"]), " patents"
    print network, ": loading data with ", " and ".join(mixNet), " fields."
    for brev in DataBrevet["brevets"]:
            #tempo = pickle.load(fic) # we only memorize needed nfo
        pat = dict ()
        for key in NeededInfo:
            if isinstance(brev[key], list) and key not in ['label', 'references', 'priority-active-indicator', 'representative', 'family lenght']:
                brev[key] = filter(None, brev[key])  #hum this should be done at the gathering processes
                if "NEANT" in brev[key]:
                    for nb in range(brev[key].count('NEANT')):
                        brev[key].remove('NEANT')
                if "empty" in brev[key]:
                    for nb in range(brev[key].count('empty')):
                        brev[key].remove('empty')
                brev[key]= flatten(brev[key])
                if key.count('date') ==0:
                    brev[key]= [cont for cont in brev[key] if cont not in ['empty', 'Empty', '']]
                if len(brev[key]) ==1: # lists of one element
                    brev[key]= brev[key][0]
            elif isinstance(brev[key], list) and key=='references':
                brev[key] = str(sum(brev[key]))
            elif isinstance(brev[key], list) and key=='priority-active-indicator':
                brev[key] = str(max(brev[key]))
            elif isinstance(brev[key], list) and key=='representative':
                if len(brev[key])==0:
                    brev[key] = "0"
                else:
                    brev[key] = str(max(brev[key]))
            elif isinstance(brev[key], list) and key=='family lenght':
                brev[key] = str(max(brev[key]))
            elif isinstance(brev[key], list) and key=='label':
                
                if len(set(brev[key]))>2:
                    print "aille aille"
                    
                else:
                    brev[key]= list(set(brev[key]))[0]
            elif isinstance (brev[key], unicode) or isinstance (brev[key], str):
                brev[key].replace('empty', '')
                brev[key].replace('Empty', '')
            pat[key] = brev[key]
        if 'CitO' in pat.keys():
            if pat['CitO'] != '' and pat['CitO'] != []:
                pat['CitO'] =[thing.replace('\n', ' ') for thing in pat['CitO']]
#            nb = prod([len(pat[cle]) for cle in pat.keys()])
#            somme+=nb
#            if nb>10000:
#                print nb, len(Patents), somme
#            for flatPat in DecoupeOnTheFly(pat, []):
#                if flatPat not in ListeBrevet:
#                    ListeBrevet.append(flatPat)
        tempoBrev = DecoupeOnTheFly(pat, ['prior-dateDate', u'family lenght', 'representative'])
        pattents = [res for res in tempoBrev if res not in ListeBrevet]
        ListeBrevet.extend(pattents)
        if pat['label'] not in Patents:
            Patents.add(pat['label'])   
            Prior[pat['label']] = pat['prior']
            Poids[pat['label']] = pat[u'family lenght']
        if pat['label'] == pat['prior']:
            Category[pat['label']] = 'Prior'
    for lab in Patents:
        temp = []
        
        for bre in [brev for brev in ListeBrevet if brev['label']==lab]:
            for cat in mixNet:
                if cat not in [u'family lenght', 'representative']:
                    if  (bre[cat],  cat) not in temp:
                        temp.append((bre[cat],  cat))
                        Dates = [] 
                        tempo = bre['date'].split('-')
                        Dates.append(datetime.date(int(tempo[0]), int(tempo[1]), int(tempo[2] )))                     
                    else:
                        pass
        
        if len(temp)>1: # This should exclude monomembers families

            if lab not in Category.keys():
                Category[lab] = 'label'
            for noeud in temp:
                if noeud[0] != lab and noeud[0] != '' and noeud[0].lower() != 'empty':
                   
                    couple =  [lab, noeud[0]]
                    appars.append((couple,Dates))
#                    if lab == u'TWI238008':
#                        print
                
            for noeud, cat in temp:
                if noeud != '' and noeud.lower() != 'empty':
                    if noeud not in Patents:
                        Category[noeud] = cat
                    else:
                        Category[noeud] = 'equivalent'
            #Building nodes properties

                
    
#    mixNet.extend(['CitP', "CitO", "CitedBy"]) #colouring as 
    
    
    rep = ndf.replace('Families', '')
    BiblioPath = '..//DATA//'+ndf+'//PatentBiblios'
    ResultPathGephi = '..//DATA//'+ndf+'//GephiFiles'
    ResultPathContent = '..//DATA//'+ndf  #+'//PatentContentsHTML'
    try:
        os.mkdir(ResultPathGephi)
    except:
        pass
  
    # CREATING THE WEIGHTED HIERARCHIC GRAPH   
    WeightDyn = dict()
    AtribDynLab = dict()
    AtribLab = dict() 
    for (source, target), datum in appars: 
        datum = [ddd for ddd in datum if isinstance(ddd, datetime.date)]

        if source not in Nodes.keys() and source != '':
                Nodes[source] = dict ()
                Nodes[source]['date'] = datum
                Nodes[source]['category'] = Category[source]
                Nodes[source]['label'] = source
                Nodes[source]['index'] = len(Nodes.keys())-1
                Nodes[source]['date']= flatten(Nodes[source]['date'])
                #Nodes[source]['pid'] = Prior[source]
                
                Nodes[source]['weight'] = Poids[source]
                if source in Patents and Nodes.has_key(Prior[source]):
                    AtribLab [Nodes[source]['index']] = Nodes[Prior[source]]['index']
        elif datum not in Nodes[source]['date']:
                Nodes[source]['date'].extend(datum)
        else:
                pass
        if target not in Nodes.keys() and target != '':
                Nodes[target] = dict ()
                Nodes[target]['date'] = datum
                Nodes[target]['category'] = Category[target]
                if Nodes[target]['category'] == 'CitO':
                    Nodes[target]['label'] = target[0:14]
                else:
                    Nodes[target]['label'] = target
                
                Nodes[target]['index'] = len(Nodes.keys())-1
                Nodes[target]['weight'] = Poids[source]
                if target in Patents and Nodes.has_key(Prior[target]):
                    AtribLab [Nodes[target]['index']] = Nodes[Prior[target]]['index']
                Nodes[target]['date']= flatten(Nodes[target]['date'])
        elif datum not in Nodes[target]['date']:
                Nodes[target]['date'].extend(datum)
        else:
                pass
        indSRC = Nodes[source]['index']
        indTGT = Nodes[target]['index']
        if (indSRC, indTGT) not in WeightDyn.keys():
            WeightDyn[(indSRC, indTGT)] = dict()
        
        for dat in datum:
            if isinstance(dat, list):
                    deb = min([dates for dates in dat])
                    fin = max([dates for dates in dat])
                    fin = datetime.date(fin.year+20, fin.month, fin.day)
            else:
                deb = min(datum)
                fin = datetime.date(dat.year+20, dat.month, dat.day) #setting endtime collaboration to 20 year after starting date....
            if int(fin.year) - int(datetime.date.today().year)>2:
                fin = datetime.date(int(datetime.date.today().year)+2, int(datetime.date.today().month), int(datetime.date.today().day))
            if len(WeightDyn[(indSRC, indTGT)])==0:
                WeightDyn[(indSRC, indTGT)] = dict()
                tempo = dict()
                tempo['value'] = 1

#                        tempo['start'] = deb.isoformat()
#                        tempo['end'] = fin.isoformat()
                WeightDyn[(indSRC, indTGT)]= tempo
                
            else:
                tempo = dict()
                tempo['value'] = WeightDyn[(indSRC, indTGT)]['value']+1
#                        tempo['start'] = [WeightDyn[(indSRC, indTGT)]['start']].append(dat.isoformat())
#                        tempo['end'] = [WeightDyn[(indSRC, indTGT)]["end"]].append(fin.isoformat())
                WeightDyn[(indSRC, indTGT)] = tempo
            attr_dict_lab = dict()
            attr_dict_weight = dict()
            if Nodes.keys().index(source) in AtribDynLab.keys():
                existant =  AtribDynLab[Nodes.keys().index(source)] ['label']['start'].split('-')
                dateActu = datetime.date (int(existant[0]), int(existant[1]), int(existant[2]))
                G1deb= min(dat, dateActu).isoformat()
                existant =  AtribDynLab[Nodes.keys().index(source)] ['label']['end'].split('-')
                dateActu = datetime.date (int(existant[0]), int(existant[1]), int(existant[2]))
                G1fin = max(fin, dateActu ).isoformat()
                G1poids = Nodes[source]['weight']  #int(AtribDynLab[Nodes.keys().index(source)] ['weight']['value']) +1
                attr_dict_lab['label'] = Nodes[source]['label']
                #attr_dict_lab['pid'] = Nodes[source]['pid']
                attr_dict_lab['start'] = G1deb
                attr_dict_lab['end'] = G1fin
                attr_dict_weight['value'] =str(G1poids)
                attr_dict_weight['start'] = G1deb
                attr_dict_weight['end'] = G1fin
                #AtribLab[Nodes.keys().index(source)]  = Nodes[source]['pid']          
                AtribDynLab[Nodes.keys().index(source)] ['label'] = copy.copy(attr_dict_lab)
                AtribDynLab[Nodes.keys().index(source)] ['weight'] = copy.copy(attr_dict_weight)
            else:
                G1deb=dat.isoformat()
                G1fin = fin.isoformat()
                G1poids = 1
                attr_dict_lab['label'] = Nodes[source]['label']
                #attr_dict_lab['pid'] = Nodes[source]['pid']
                attr_dict_lab['start'] = G1deb
                attr_dict_lab['end'] = G1fin
                attr_dict_weight['value'] =str(G1poids)
                attr_dict_weight['start'] = G1deb
                attr_dict_weight['end'] = G1fin
                AtribDynLab[Nodes.keys().index(source)] = dict()
     #           AtribLab[Nodes.keys().index(source)] = Nodes[source]['pid']
                
                AtribDynLab[Nodes.keys().index(source)] ['label'] = copy.copy(attr_dict_lab)
                AtribDynLab[Nodes.keys().index(source)] ['weight'] = copy.copy(attr_dict_weight)
            #setting node properties (target)
            if Nodes.keys().index(target) in AtribDynLab.keys():
                existant =  AtribDynLab[Nodes.keys().index(target)] ['label']['start'].split('-')
                dateActu = datetime.date (int(existant[0]), int(existant[1]), int(existant[2]))
                G1deb= min(dat, dateActu).isoformat()
                existant =  AtribDynLab[Nodes.keys().index(target)] ['label']['end'].split('-')
                dateActu = datetime.date (int(existant[0]), int(existant[1]), int(existant[2]))
                G1fin = max(fin, dateActu ).isoformat()
                G1poids = Nodes[target]['weight']#int(AtribDynLab[Nodes.keys().index(target)] ['weight']['value']) +1
                attr_dict_lab['label'] = Nodes[target]['label']
                #attr_dict_lab['pid'] = Nodes[target]['pid']
                attr_dict_lab['start'] = G1deb
                attr_dict_lab['end'] = G1fin
                attr_dict_weight['value'] =str(G1poids)
                attr_dict_weight['start'] = G1deb
                attr_dict_weight['end'] = G1fin
    #            AtribLab[Nodes.keys().index(target)] = Nodes[target]['pid']
                AtribDynLab[Nodes.keys().index(target)] ['label'] =copy.copy( attr_dict_lab)
                AtribDynLab[Nodes.keys().index(target)] ['weight'] = copy.copy(attr_dict_weight)
            else:
                G1deb=dat.isoformat()
                G1fin = fin.isoformat()
                G1poids = 1
                attr_dict_lab['label'] = Nodes[target]['label']
               # attr_dict_lab['pid'] = Nodes[target]['pid']
                attr_dict_lab['start'] = G1deb
                attr_dict_lab['end'] = G1fin
                attr_dict_weight['value'] =str(G1poids)
                attr_dict_weight['start'] = G1deb
                attr_dict_weight['end'] = G1fin
                
                AtribDynLab[Nodes.keys().index(target)] = dict()
   #             AtribLab[Nodes.keys().index(target)] = Nodes[target]['pid']
                AtribDynLab[Nodes.keys().index(target)] ['label'] = copy.copy(attr_dict_lab)
                AtribDynLab[Nodes.keys().index(target)] ['weight'] = copy.copy(attr_dict_weight)



            G1.add_node(indSRC, attr_dict={'label':Nodes[source]['label'], 'category':Nodes[source]['category']})
            G1.add_node(indTGT, attr_dict={'label':Nodes[target]['label'], 'category':Nodes[target]['category']})
            if Nodes[target]['category'] == 'CitedBy':
                G1.add_edge(indTGT, indSRC, attr_dict= WeightDyn[(indSRC, indTGT)])# reverse link for citind the patent

            else:
                G1.add_edge(indSRC, indTGT, attr_dict= WeightDyn[(indSRC, indTGT)])#
#                G2.add_edge(indSRC, indTGT, attr_dict)
#             
            #print
    for key in Prior.keys():
        if key not in AtribLab.keys():
            AtribLab[Nodes.keys().index(key)] = Nodes.keys().index(Prior[key])
    for key in Nodes.keys():
        if Nodes[key]['index'] not in AtribLab.keys():
             AtribLab[Nodes[key]['index']] = Nodes[key]['index'] # loop for no hierachical structure
    AtribDyn=dict()
    Atrib = dict()
    for noeud in AtribDynLab.keys():
        AtribDyn[noeud] = dict()
        AtribDyn[noeud]['id']= AtribDynLab.keys().index(noeud)
        AtribDyn[noeud]['start']= AtribDynLab[noeud]['label']['start']
        AtribDyn[noeud]['end']= AtribDynLab[noeud]['label']['end']
        AtribDyn[noeud]['label']= AtribDynLab[noeud]['label']['label']
 
#        if noeud in Patents:
#            AtribDyn[noeud]['pid']= AtribDynLab[noeud]['pid']
   #     Atrib[noeud] = AtribDynLab[noeud]['label']['label']
    nx.set_node_attributes(G1, 'id' , AtribDyn)

#    Atrib = OrderedDict()
#    for noeud in AtribDynLab.keys(): # ?????????
##        AtribDyn[noeud] = AtribDynLab[noeud]['weight']
#        Atrib [noeud] = AtribLab[noeud] ['pid']
    nx.set_node_attributes(G1,  'pid', AtribLab)
    for noeud in AtribDynLab.keys():
        AtribDyn[noeud] = AtribDynLab[noeud]['weight']
#        Atrib[noeud] = dict()
#        if noeud in Patents:
#            Atrib[noeud]['pid']= AtribDynLab[noeud]['pid']
#        else:
#            Atrib[noeud]['pid']= ""
#    nx.set_node_attributes(G1,  'pid', Atrib)
    nx.set_node_attributes(G1,  'weight', AtribDyn)

    nx.write_gpickle(G1, temporPath+network)
