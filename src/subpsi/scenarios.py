"""Explicit simulation interventions, independent data roles, fixed classifier."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from .core import Group

SCENARIOS={
 "S0":"No change",
 "S1":"One-group measurement shift",
 "S2":"Opposing intersection shifts",
 "S3":"Benign unused-feature shift",
 "S4":"Outcome change; inputs unchanged",
 "S5":"Group-composition change",
}


def predefined_groups():
    return [Group("all")]+[Group(f"{c}={v}",((c,v),),"single") for c in ["A","B"] for v in [0,1]]+[
        Group(f"A={a},B={b}",(("A",a),("B",b)),"intersection") for a in [0,1] for b in [0,1]]


def generate(n,rng,scenario="S0",active=False,share=0.1,magnitude=1.25,role="sample"):
    # All four intersections have equal mass for S2; exact distributional
    # cancellation comes from swapping +0.8 and -0.8 means within each margin.
    if scenario=="S2": share=0.5
    if active and scenario=="S5": share=0.4
    a=rng.binomial(1,share,n); b=rng.binomial(1,0.5,n)
    parity=np.where(a==b,1,-1)
    mean=0.8*parity if scenario=="S2" else 0.8*a
    latent=rng.normal(mean,1,n)
    nuisance=rng.normal(0,1,n)
    y=rng.binomial(1,expit(1.5*latent))
    signal=latent.copy()
    if active:
        if scenario=="S1": signal += magnitude*(a==1)
        elif scenario=="S2": signal -= 1.6*parity
        elif scenario=="S3": nuisance += magnitude
        elif scenario=="S4": y=np.where(a==1,1-y,y)
    return pd.DataFrame({"id":[f"{role}:{i}" for i in range(n)],"A":a,"B":b,"signal":signal,"nuisance":nuisance,"y":y})


def assert_disjoint(*frames):
    seen=set()
    for frame in frames:
        ids=set(frame["id"])
        if len(ids)!=len(frame) or seen&ids: raise ValueError("data roles overlap or contain duplicate IDs")
        seen |= ids


def fit_logistic(frame,features=("signal",)):
    x=frame[list(features)].to_numpy(float); y=frame.y.to_numpy(float)
    mean=x.mean(axis=0); scale=x.std(axis=0); scale[scale==0]=1
    z=np.column_stack([np.ones(len(x)),(x-mean)/scale])
    def objective(w):
        scores=z@w
        # Average log loss plus a fixed small L2 penalty, intercept unpenalized.
        penalty=0.001*np.dot(w[1:],w[1:])/2
        grad=z.T@(expit(scores)-y)/len(y)
        grad[1:]+=0.001*w[1:]
        return np.mean(np.logaddexp(0,scores)-y*scores)+penalty,grad
    fit=minimize(objective,np.zeros(z.shape[1]),jac=True,method="L-BFGS-B")
    if not fit.success: raise RuntimeError(f"logistic fit failed: {fit.message}")
    return {"features":list(features),"mean":mean.tolist(),"scale":scale.tolist(),"weights":fit.x.tolist()}


def predict(model,frame):
    z=(frame[model["features"]].to_numpy(float)-model["mean"])/model["scale"]
    return (np.column_stack([np.ones(len(z)),z])@model["weights"]>=0).astype(int)


def evaluate(model,frame,groups):
    prediction=predict(model,frame); y=frame.y.to_numpy(int); rows=[]
    for group in groups:
        mask=group.mask(frame); positive=mask&(y==1); negative=mask&(y==0)
        np_,nn=int(positive.sum()),int(negative.sum())
        rows.append({"group":group.name,"n":int(mask.sum()),"positive":np_,"negative":nn,
                     "tpr":float(prediction[positive].mean()) if np_ else None,
                     "fpr":float(prediction[negative].mean()) if nn else None,
                     "accuracy":float((prediction[mask]==y[mask]).mean()) if mask.any() else None})
    return rows


def tpr_gap(rows):
    values={r["group"]:r["tpr"] for r in rows}
    if values.get("A=0") is None or values.get("A=1") is None: return None
    return abs(values["A=1"]-values["A=0"])
