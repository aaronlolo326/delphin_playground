import networkx as nx
from pygraphviz import AGraph
import re
from random import randrange

class Delphin_DiGraphs:
    def __init__(self,text):
        self.text = text
        self.erg_derivation_dg = nx.DiGraph()
        self.syn_tree_dg = nx.DiGraph()
        self.dmrs_dg = nx.DiGraph()
        self.eds_dg = nx.DiGraph()
        
    def mrp_json_to_directed_graph(mrp_json):
        pass
    
    @classmethod
    def from_string(cls, date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        date1 = cls(day, month, year)
        return date1

    @staticmethod
    def is_date_valid(date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        return day <= 31 and month <= 12 and year <= 3999

    @classmethod
    def test_print(cls):
        print ("working wel~")
    
    @staticmethod
    def to_seq_ag(ag, top_node_id, text, simplified=True):
        '''
        Add position attributes to ag graph.
        return an pygraphviz AGraph.
        '''
        #if ag_type == 'dmrs':
        #print (ag)
        #print ()
        try:
            for node_id in ag.iternodes():
                node = ag.get_node(node_id)
                #print (node.attr['label'])
                an = [(int(re.split('[( , )]',prop_str.strip())[1]),int(re.split('[( , )]',prop_str.strip())[2]))
                                    for prop_str in node.attr['label'].split("\n") if prop_str.startswith("(")]
                an_from, an_to = an[0][0], an[0][1]
                pos_y = 0.0
                if node.attr['label'].split("\n")[0][0] != '_':
                    pos_y = sum([ord(c) for c in node.attr['label'].split("\n")[0]])%47 * 11
                    print (pos_y)
            
                node.attr['pos']="%f,%f"%(float(an_from+an_to)*21,pos_y)
                if node_id == str(top_node_id):
                    node.attr['shape'] = "box"
                ag.edge_attr['fontsize'] = 8
                if simplified:
                    label_list = node.attr['label'].split("\n")
                    node.attr['label'] = label_list[0] + "\n" + label_list[-1]
        except Exception as e:
            print (e)
        return ag
    
    def init_syn_tree(self,syn_tree):
        '''
        First convert syntactic tree to dictionary {'id':,'children':[{...}]},
        then convert to DiGraph and store
        '''
        id_in = 0
        syn_tree_dict = dict()
        def dfs_to_dict(par_node,syn_tree_node):
            nonlocal id_in
            par_node['id'] = id_in
            id_in += 1
            par_node['label'] = syn_tree_node[0]
            if len(syn_tree_node) > 1:
                par_node['children'] = []
                for idx in range(1,len(syn_tree_node)):
                    par_node['children'].append(dict())
                    dfs_to_dict(par_node['children'][idx-1],syn_tree_node[idx])
        dfs_to_dict(syn_tree_dict,syn_tree)
        
        syn_dg_data = syn_tree_dict
        self.syn_tree_dg = nx.readwrite.json_graph.tree_graph(syn_dg_data)
    
    def init_erg_deriv(self,deriv):
        NON_TERM_FIELDS = ['entity','score','start','end']
        TERM_FIELDS = ['form']
#         print (
#             getattr(deriv,'id'),
#             deriv.entity,
#             deriv.score,
#             deriv.start,
#             deriv.end,
#             deriv.daughters,
#     #         deriv.head,
#             deriv.type,
#         )
        print ("\n")
        
        def add_node_edge(par_node,node):
            #print (node.to_dict())
            if hasattr(node,'id'):
                #non-terminal nodes
                FIELDS = NON_TERM_FIELDS
                node_id = getattr(node,'id')
                self.erg_derivation_dg.add_node(node_id)
                node_info_texts = [str(getattr(node,FIELD)) for FIELD in FIELDS]
                s_e = "("+node_info_texts[-2]+","+node_info_texts[-1]+")"
                node_info_texts[-2] = s_e
                del node_info_texts[-1]
            else:
                #terminal nodes
                FIELDS = TERM_FIELDS
                node_id = getattr(node,'tokens')[0].id
                self.erg_derivation_dg.add_node(node_id)
                node_info_texts = [str(getattr(node,FIELD)) for FIELD in FIELDS]

            self.erg_derivation_dg.nodes[node_id]['label'] = '\n'.join(node_info_texts)
            if par_node != None:
                self.erg_derivation_dg.add_edge(par_node.id,node_id)
        
        #add nodes
        def dfs(par_node,deriv_node):
            add_node_edge(par_node,deriv_node)
            if hasattr(deriv_node,'daughters'):
                [dfs(deriv_node,daughter) for daughter in deriv_node.daughters]
 
        
        dfs(None,deriv)
        
    
    def init_dmrsjson(self,dmrsjson):
        for node in dmrsjson['nodes']:
            self.dmrs_dg.add_node(node['nodeid'])
            node_info_texts = node['predicate']+"\n"
            if 'sortinfo' in node:
                for prop in node['sortinfo']:
                    node_info_texts = node_info_texts + prop + ": " + node['sortinfo'][prop] + "\n"
            node_info_texts = node_info_texts + "(" + str(node['lnk']['from']) + "," + str(node['lnk']['to']) + ")"
            self.dmrs_dg.nodes[node['nodeid']]['label'] = node_info_texts
        for edge in dmrsjson['links']:
            self.dmrs_dg.add_edge(edge['from'],edge['to'], label=edge['rargname']+"/"+edge['post'])
    
    def init_edsjson(self,edsjson):
        for node_id in edsjson['nodes']:
            self.eds_dg.add_node(node_id)
            node = edsjson['nodes'][node_id]
            node_info_texts = node['label']+"\n"
            if 'properties' in node:
                for prop in node['properties']:
                    node_info_texts = node_info_texts + prop + ": " + node['properties'][prop] + "\n"
            node_info_texts = node_info_texts + "(" + str(node['lnk']['from']) + "," + str(node['lnk']['to']) + ")"
            self.eds_dg.nodes[node_id]['label'] = node_info_texts
        for node_id in edsjson['nodes']:
            node = edsjson['nodes'][node_id]
            for out_edge in node['edges']:
                self.eds_dg.add_edge(node_id,node['edges'][out_edge],label=out_edge)
    
if  __name__ =='__main__':
    pass