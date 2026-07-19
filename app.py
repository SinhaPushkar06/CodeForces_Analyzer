import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.title("🚀 Codeforces Analyzer")
handle = st.text_input("Enter Codeforces Handle")
page = st.sidebar.radio(
    "Choose Analysis",
    [
        "Profile",
        "Submissions",
        "Rating Wise Questions",
        "Contest Info",
        "Submission Stats",
        "Tags",
        "Weak Topics",
        "Correct Problems Solved",
        "Rating Graph",
    ]
)

def get_info(handle):
  try:
      info = requests.get(
          f"https://codeforces.com/api/user.info?handles={handle}",
          timeout=10
      ).json()

  except requests.exceptions.RequestException as e:
      st.error(f"Request failed: {e}")
      return None

  if info["status"] == "FAILED":
      st.error(info["comment"])
      return None

  infor = pd.DataFrame(info["result"])

  if infor.empty:
      st.error("No profile data found.")
      return None
  return infor


def get_profile(infor):
  information=pd.DataFrame({
      'First_Name':infor.get('firstName'),
      'Last_Name':infor.get('lastName'),
      'Max_Rating':infor.get('maxRating'),
      'Current_Rating':infor.get('rating'),
      'Max_Rank':infor.get('maxRank'),
      'Country':infor.get('country'),
      'Organisation/College/University':infor.get('organization'),
  })
  return information


def get_submission(handle):
  try:
    sub = requests.get(
        f"https://codeforces.com/api/user.status?handle={handle}",
        timeout=10
    ).json()

  except requests.exceptions.RequestException as e:
    st.error(f"Request failed: {e}")
    return None

  if sub["status"] == "FAILED":
    st.error(sub["comment"])
    return None

  submission=pd.DataFrame(sub['result'])
  submission.rename(columns={'passedTestCount': 'Rating'}, inplace=True)
  submission['Rating']=submission['problem'].apply(lambda x:x.get("rating"))
  submission['Problem Name']=submission['problem'].apply(lambda x:x['index']+" - "+x['name'])
  submission['author']=submission['author'].apply(lambda x:x["participantType"])
  submission=submission[['id','contestId','creationTimeSeconds','relativeTimeSeconds','Problem Name','author','Rating','programmingLanguage','verdict','testset','timeConsumedMillis','memoryConsumedBytes','problem']]
  submission.rename(columns={'creationTimeSeconds': 'Date'}, inplace=True)
  submission['Date'] = pd.to_datetime(submission['Date'],unit='s')

  submission['relativeTimeSeconds'] = submission['relativeTimeSeconds'].apply(
      lambda x: '-' if x == 2147483647 else str(pd.to_timedelta(x, unit='s'))
  )

  return submission
def wrong_sub(submm):
   wt=pd.DataFrame(submm[submm['verdict']!='OK']['problem'].tolist())
   return wt['tags'].explode().value_counts()

def get_rating(handle):
  try:
    rating=requests.get("https://codeforces.com/api/user.rating?handle={}".format(handle),timeout=10).json()
  except requests.exceptions.RequestException as e:
     st.error(f"Request failed: {e}")
     return None
  if rating["status"]=="FAILED":
     st.error(rating["comment"])
     return None
  ratings=pd.DataFrame(rating['result'])

  return ratings

def get_rating_q(r):
  return r.drop_duplicates(subset=['contestId', 'Problem Name'])['Rating'].value_counts().sort_index()

def get_prblm_sol(r):
  problems_solved=pd.DataFrame(r['problem'].tolist()).drop_duplicates(subset=["name"])
  return problems_solved

def get_tags(r):
  tags=get_prblm_sol(r)['tags'].explode().value_counts()
  return tags

def get_substat(submm):
  x=submm['verdict'].value_counts()
  x['Acceptance Rate']=(x['OK']/x.sum())*100
  return x

def get_rating_graph(ratt):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(ratt)+1)),
            y=ratt["newRating"],
            mode="lines+markers",
            line=dict(width=3, color="gold"),
            marker=dict(size=7),
            customdata=ratt["contestName"],
            hovertemplate=
            "<b>%{customdata}</b><br>" +
            "Rating: %{y}<extra></extra>"
        )
    )
    bands = [
        (0,1200,"#CCCCCC"),       # Newbie
        (1200,1400,"#77FF77"),    # Pupil
        (1400,1600,"#77DDBB"),    # Specialist
        (1600,1900,"#AAAAFF"),    # Expert
        (1900,2100,"#FF88FF"),    # Candidate Master
        (2100,2300,"#FFCC88"),    # Master
        (2300,2400,"#FFBB55"),    # International Master
        (2400,2600,"#FF7777"),    # Grandmaster
        (2600,3000,"#FF3333"),    # International GM
        (3000,4000,"#AA0000"),    # Legendary GM
    ]

    for low, high, color in bands:
        fig.add_hrect(
            y0=low,
            y1=high,
            fillcolor=color,
            opacity=0.25,
            line_width=0
        )

    fig.update_layout(
        title="📈 Rating Progress",
        template="plotly_dark",
        xaxis_title="Contest Number",
        yaxis_title="Rating",
        hovermode="x unified",
        height=600,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

if st.button("Analyze"):

    infor = get_info(handle)
    submm=get_submission(handle)
    ratt=get_rating(handle)
    

    if(infor is not None and submm is not None and ratt is not None):
        r=submm[submm['verdict']=='OK'].reset_index(drop=True)
        if page=="Profile":
           st.dataframe(get_profile(infor))
        elif page=="Submissions":
           st.dataframe(submm.drop(columns=['problem']))
        elif page=="Contest Info":
           st.dataframe(ratt)
        elif page=="Tags":
           st.dataframe(get_tags(r))
        elif page=="Rating Graph":
           get_rating_graph(ratt)
        elif page=="Correct Problems Solved":
           st.dataframe(get_prblm_sol(r))
        elif page=="Rating Wise Questions":
           st.dataframe(get_rating_q(r))
        elif page=="Submission Stats":
           st.dataframe(get_substat(submm))
        elif page=="Weak Topics":
           st.dataframe(wrong_sub(submm))
           
