# Copyright 2026 J Joe

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
_H='method'
_G='function'
_F='kind'
_E='dst'
_D=False
_C='class'
_B=True
_A=None
import ast,json,sys
from collections import defaultdict
from dataclasses import dataclass,field
from pathlib import Path
from typing import Optional
@dataclass
class Symbol:
	module:str;name:str;kind:str;cls:Optional[str]=_A;file:Optional[str]=_A;lines:Optional[tuple[int,int]]=_A
	def qname(A):
		if A.cls:return f"{A.module}.{A.cls}.{A.name}"
		return f"{A.module}.{A.name}"
@dataclass
class Edge:
	src:str;dst:str;kind:str;via:Optional[str]=_A
	def to_dict(A):
		B={'src':A.src,_E:A.dst,_F:A.kind}
		if A.via is not _A:B['via']=A.via
		return B
	def to_list(A):return[A.src,A.dst,A.kind]+([A.via]if A.via else[])
class Graph:
	def __init__(A):A.symbols=[];A.edges=[];A._sym_by_qname={};A._edge_keys=set();A._uses=defaultdict(list);A._used_by=defaultdict(list)
	def add_symbol(B,sym):A=sym;B.symbols.append(A);B._sym_by_qname[A.qname()]=A
	def get_symbol(A,qname):return A._sym_by_qname.get(qname)
	def find(F,name):
		B=name;D=[]
		for A in F.symbols:
			E=A.qname();C=f"{A.cls}.{A.name}"if A.cls else _A
			if E==B or E.endswith(f".{B}")or C and(C==B or C.endswith(f".{B}")):D.append(A)
		return D
	def resolve_name(D,name,prefer_module=_A):
		A=prefer_module;B=[A for A in D.symbols if A.name==name]
		if A:
			C=[B for B in B if B.module==A]
			if C:return C
		return B
	def resolve_method(A,cls_name,method):return[A for A in A.symbols if A.cls==cls_name and A.name==method]
	def add_edge(A,src,dst,kind,via=_A):
		C=dst;B=src
		if not B or not C or B==C:return
		E=B,C,kind,via
		if E in A._edge_keys:return
		A._edge_keys.add(E);D=Edge(B,C,kind,via);A.edges.append(D);A._uses[B].append(D);A._used_by[C].append(D)
	def query(C,name):
		H=[]
		for B in C.find(name):
			D=B.qname();F=list(C._uses.get(D,[]));G=list(C._used_by.get(D,[]))
			if B.kind==_C:
				I=D+'.';J={(A.src,A.dst,A.kind,A.via)for A in F};K={(A.src,A.dst,A.kind,A.via)for A in G}
				for A in C.edges:
					E=A.src,A.dst,A.kind,A.via
					if A.src.startswith(I)and E not in J:F.append(A);J.add(E)
					if A.dst.startswith(I)and E not in K:G.append(A);K.add(E)
			def L(e,name_field):
				A={'name':getattr(e,name_field),_F:e.kind}
				if e.via is not _A:A['via']=e.via
				return A
			H.append({'symbol':D,_F:B.kind,'file':B.file,'lines':B.lines,'uses':[L(A,_E)for A in _dedup_edges(F)],'used_by':[L(A,'src')for A in _dedup_edges(G)]})
		return H
def _dedup_edges(edges):
	B=set();C=[]
	for A in edges:
		D=A.src,A.dst,A.kind,A.via
		if D not in B:B.add(D);C.append(A)
	return sorted(C,key=lambda e:(e.dst if hasattr(e,_E)else'',e.src,e.kind,e.via or''))
class DefCollector(ast.NodeVisitor):
	def __init__(A,module,file,graph):A.module=module;A.file=file;A.graph=graph;A._class_stack=[];A._func_depth=0
	def visit_ClassDef(A,node):B=node;C=B.lineno,B.end_lineno;A.graph.add_symbol(Symbol(A.module,B.name,_C,file=A.file,lines=C));A._class_stack.append(B.name);A.generic_visit(B);A._class_stack.pop()
	def visit_FunctionDef(A,node):
		B=node;C=B.lineno,B.end_lineno
		if A._class_stack:D=Symbol(A.module,B.name,_H,cls=A._class_stack[-1],file=A.file,lines=C)
		else:D=Symbol(A.module,B.name,_G,file=A.file,lines=C)
		A.graph.add_symbol(D);A._func_depth+=1;A.generic_visit(B);A._func_depth-=1
	visit_AsyncFunctionDef=visit_FunctionDef
	def _register_var(A,target,node):
		B=target
		if A._func_depth>0 or A._class_stack:return
		if isinstance(B,ast.Name):
			C=A.graph.resolve_name(B.id,A.module)
			if not any(A.kind in(_C,_G)for A in C):D=node.lineno,node.end_lineno;A.graph.add_symbol(Symbol(A.module,B.id,'var',file=A.file,lines=D))
	def visit_Assign(B,node):
		A=node
		for C in A.targets:B._register_var(C,A)
		B.generic_visit(A)
	def visit_AnnAssign(B,node):A=node;B._register_var(A.target,A);B.generic_visit(A)
@dataclass
class TypeInfo:cls_sym:Optional[Symbol];sym:Optional[Symbol];is_instance:bool=_D
class TypeInferrer:
	def __init__(A,graph):A.graph=graph;A.var_type=defaultdict(dict);A.func_returns={}
	def infer(B,trees):
		for E in range(10):
			A=_D
			for(C,D)in trees:A|=B._process_module(C,D)
			if not A:break
	def _process_module(C,tree,module):
		D=module;B=_D
		for A in ast.walk(tree):
			if isinstance(A,(ast.FunctionDef,ast.AsyncFunctionDef)):B|=C._process_func(A,D)
			elif isinstance(A,(ast.Assign,ast.AnnAssign)):B|=C._process_module_assign(A,D)
		return B
	def _process_module_assign(C,node,module):
		G=module;A=node;F=_D;D=G
		if isinstance(A,ast.Assign):
			for E in A.targets:
				if isinstance(E,ast.Name):
					B=C._infer_expr(A.value,G,D)
					if B and E.id not in C.var_type[D]:C.var_type[D][E.id]=B;F=_B
					elif B and C.var_type[D].get(E.id)!=B:C.var_type[D][E.id]=B;F=_B
		elif isinstance(A,ast.AnnAssign):
			if isinstance(A.target,ast.Name)and A.value:
				B=C._infer_expr(A.value,G,D)
				if B and C.var_type[D].get(A.target.id)!=B:C.var_type[D][A.target.id]=B;F=_B
		return F
	def _process_func(A,node,module):
		F=module;E=node;N=A.graph.resolve_name(E.name,F);L=next(iter(N),_A)
		if not L:return _D
		G=L.qname();D=G;I=_D
		if E.returns and isinstance(E.returns,ast.Name):
			J=[A for A in A.graph.resolve_name(E.returns.id,F)if A.kind==_C]
			if J and A.func_returns.get(G)!=J[0]:A.func_returns[G]=J[0];I=_B
		C=dict(A.var_type.get(D,{}))
		for B in ast.walk(E):
			if isinstance(B,(ast.Assign,ast.AnnAssign)):
				if isinstance(B,ast.Assign):
					for M in B.targets:
						if isinstance(M,ast.Name):
							H=A._infer_expr(B.value,F,D,C)
							if H:C[M.id]=H
				elif isinstance(B.target,ast.Name)and B.value:
					H=A._infer_expr(B.value,F,D,C)
					if H:C[B.target.id]=H
			elif isinstance(B,ast.Return)and B.value:
				K=A._infer_class_from_expr(B.value,F,D,C)
				if K and A.func_returns.get(G)!=K:A.func_returns[G]=K;I=_B
		if C!=A.var_type.get(D):A.var_type[D]=C;I=_B
		return I
	def _infer_expr(D,node,module,scope,local_env=_A):
		E=module;A=node;B=local_env or{}
		if isinstance(A,ast.Name):
			if A.id in B:return B[A.id]
			F=D.graph.resolve_name(A.id,E)
			if F:C=F[0];return TypeInfo(cls_sym=C if C.kind==_C else _A,sym=C,is_instance=_D)
			return
		if isinstance(A,ast.Call):return D._infer_call(A,E,scope,B)
	def _infer_call(D,node,module,scope,env):
		A=node.func
		if isinstance(A,ast.Name):
			F=D.graph.resolve_name(A.id,module)
			if F:
				C=F[0]
				if C.kind==_C:return TypeInfo(cls_sym=C,sym=C,is_instance=_B)
				B=D.func_returns.get(C.qname())
				if B:return TypeInfo(cls_sym=B,sym=B,is_instance=_B)
				return TypeInfo(cls_sym=_A,sym=C,is_instance=_D)
		if isinstance(A,ast.Attribute)and isinstance(A.value,ast.Name):
			E=env.get(A.value.id)
			if E and E.is_instance and E.cls_sym:
				G=D.graph.resolve_method(E.cls_sym.name,A.attr)
				if G:
					B=D.func_returns.get(G[0].qname())
					if B:return TypeInfo(cls_sym=B,sym=B,is_instance=_B)
			if A.value.id=='self':0
	def _infer_class_from_expr(E,node,module,scope,env):
		D=env;A=node;B=E._infer_expr(A,module,scope,D)
		if B and B.is_instance and B.cls_sym:return B.cls_sym
		if isinstance(A,ast.Name)and A.id in D:
			C=D[A.id]
			if C and C.is_instance and C.cls_sym:return C.cls_sym
	def type_of_var(A,scope,var):return A.var_type.get(scope,{}).get(var)
	def return_class(A,func_qname):return A.func_returns.get(func_qname)
class EdgeEmitter(ast.NodeVisitor):
	def __init__(A,module,graph,ti):B=module;A.module=B;A.graph=graph;A.ti=ti;A._class_stack=[];A._func_stack=[];A._scope_stack=[B]
	@property
	def _current_class(self):return self._class_stack[-1]if self._class_stack else _A
	@property
	def _current_func(self):return self._func_stack[-1]if self._func_stack else _A
	@property
	def _scope(self):return self._scope_stack[-1]
	def _caller(A):
		if A._current_func:return A._current_func.qname()
		return A._scope
	def _type_of(A,var):
		B=A.ti.type_of_var(A._scope,var)
		if B:return B
		return A.ti.type_of_var(A.module,var)
	def _resolve_call(A,node):
		D=node.func;E=[]
		if isinstance(D,ast.Name):
			B=A._type_of(D.id)
			if B and B.is_instance and B.cls_sym:
				I=A.graph.resolve_method(B.cls_sym.name,'__call__');H=f"{D.id}()"
				for C in I:E.append((C,H))
				E.append((B.cls_sym,H))
			else:
				for C in A.graph.resolve_name(D.id,A.module):E.append((C,_A))
		elif isinstance(D,ast.Attribute):
			F=D.attr;G=D.value
			if isinstance(G,ast.Name):
				if G.id=='self'and A._current_class:
					for C in A.graph.resolve_method(A._current_class,F):E.append((C,_A))
				else:
					B=A._type_of(G.id)
					if B and B.is_instance and B.cls_sym:
						H=f"{G.id}.{F}"
						for C in A.graph.resolve_method(B.cls_sym.name,F):E.append((C,H))
					else:
						for C in A.graph.resolve_name(F,A.module):E.append((C,f"{G.id}.{F}"))
		return E
	def visit_ClassDef(A,node):A._class_stack.append(node.name);A.generic_visit(node);A._class_stack.pop()
	def visit_FunctionDef(A,node):B=next((B for B in A.graph.symbols if B.name==node.name and B.module==A.module and B.cls==A._current_class),_A);A._func_stack.append(B);A._scope_stack.append(B.qname()if B else A._scope);A.generic_visit(node);A._scope_stack.pop();A._func_stack.pop()
	visit_AsyncFunctionDef=visit_FunctionDef
	def visit_Assign(A,node):
		B=node;C=_A
		if not A._current_func:
			D=[A.id for A in B.targets if isinstance(A,ast.Name)]
			if D:C=A._scope_stack[-1];A._scope_stack[-1]=f"{A.module}.{D[0]}"
		A._emit_rhs_refs(B.value);A.generic_visit(B)
		if C is not _A:A._scope_stack[-1]=C
	def visit_AnnAssign(A,node):
		B=node;C=_A
		if not A._current_func and isinstance(B.target,ast.Name):C=A._scope_stack[-1];A._scope_stack[-1]=f"{A.module}.{B.target.id}"
		if B.value:A._emit_rhs_refs(B.value)
		A.generic_visit(B)
		if C is not _A:A._scope_stack[-1]=C
	def _emit_rhs_refs(A,node,dict_key=_A):
		C=dict_key;B=node
		if isinstance(B,ast.Dict):
			for(D,G)in zip(B.keys,B.values):
				if isinstance(D,ast.Constant):E=D.value
				else:E=_A
				A._emit_rhs_refs(G,dict_key=E)
		elif isinstance(B,ast.Name):
			H=A.graph.resolve_name(B.id,A.module)
			for F in H:
				if F.kind in(_G,_C,_H):I=f'{A._var_name()}["{C}"]'if C is not _A else _A;A.graph.add_edge(A._caller(),F.qname(),'ref',via=I)
		elif isinstance(B,(ast.List,ast.Tuple,ast.Set)):
			for J in B.elts:A._emit_rhs_refs(J,dict_key=C)
	def _var_name(A):B=A._scope;return B.split('.')[-1]
	def visit_Call(A,node):
		F='call';B=node;D=A._caller()
		for(C,E)in A._resolve_call(B):
			A.graph.add_edge(D,C.qname(),F,via=E)
			if C.kind==_C and E is _A:
				for G in A.graph.resolve_method(C.name,'__init__'):A.graph.add_edge(D,G.qname(),F,via=_A)
		for H in B.args:A.visit(H)
		for I in B.keywords:A.visit(I.value)
def _module_name(root,file):
	try:A=file.with_suffix('').relative_to(root);return'.'.join(A.parts)
	except ValueError:return file.stem
def _collect_files(target):
	A=Path(target)
	if A.is_file():return A.parent,[A]
	return A,list(A.rglob('*.py'))
def build(target):
	G,H=_collect_files(target);B=Graph();E=[]
	for A in H:
		try:I=A.read_text(encoding='utf-8',errors='replace');C=ast.parse(I,filename=str(A))
		except SyntaxError:continue
		D=_module_name(G,A);E.append((C,D,str(A)));DefCollector(D,str(A),B).visit(C)
	F=TypeInferrer(B);F.infer([(A,B)for(A,B,C)in E])
	for(C,D,J)in E:EdgeEmitter(D,B,F).visit(C)
	return B
def main():
	if len(sys.argv)<2:print(__doc__,file=sys.stderr);sys.exit(1)
	A=build(sys.argv[1])
	if len(sys.argv)==2:print(json.dumps([A.to_list()for A in A.edges],indent=2))
	else:
		B=A.query(sys.argv[2])
		if not B:print(f"No symbol found matching {sys.argv[2]!r}",file=sys.stderr);sys.exit(1)
		print(json.dumps(B,indent=2))
if __name__=='__main__':main()
