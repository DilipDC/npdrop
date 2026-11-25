
---iqr-----
q1=df['Annual Income (k$)'].quantile(0.25)
q3=df['Annual Income (k$)'].quantile(0.75)
iqr=q3-q1
upper_limit=q1+1.5*iqr
lower_limit=q3-1.5*iqr
men=df['Annual Income (k$)'].mean()
df['Annual Income (k$)']=df['Annual Income (k$)'].mask((df['Annual Income (k$)']>upper_limit)|(df['Annual Income (k$)']<lower_limit),men)


--------std---------

men=df['Spending Score (1-100)'].mean()
std=df['Spending Score (1-100)'].std()
lower_limit=men-3*std