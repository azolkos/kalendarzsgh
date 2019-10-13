from flask import Flask, render_template, request, jsonify, Response, url_for, redirect
import os, pandas as pd, numpy as np

app = Flask( __name__)

@app.route( '/favicon.ico')
def favicon():
    return redirect( url_for( 'static', filename='favicon.ico'))

PATH = 'harmonogramy/MGR'
SMMD = 'harmonogram zajec SD_NP 19_20 zima 7_10_2019.xlsx'

### no kurwa wiadomo ze tak latwo na tym sghu sie nie da kurwa nawet exportowac z Celcata nie potrafia spojnie
# files = []
# for r, d, f in os.walk( PATH):
#     for file in f:
#         files.append( os.path.join( PATH, file))
# xls = []
# for file in files:
#     df = pd.read_excel( file, header=1)
#     xls.append( df)
# data = pd.concat( xls, axis=0, ignore_index=True)

smmd = pd.read_excel( os.path.join( PATH, SMMD), header=1)
smmd['Sygnatura'] = smmd['Przedmiot'].astype(str).str[0:11]
smmd['Nazwa przedmiotu'] = smmd['Przedmiot'].astype(str).str[12:]
smmd['ID'] = smmd.index

def convert( df, rows):
    # legacy for other method of input: SYGNATURY (list of strings), GRUPY (list of tuples (syg, gr))
    # choice_set = df[ df[['Sygnatura', 'Numer grupy']].apply(tuple, 1).isin( GRUPY) | ( df['Sygnatura'].isin( SYGNATURY) & (df['Forma'] == 'Wykład'))]
    choice_set = df.loc[rows,]
    gcal = pd.DataFrame()
    gcal['Subject'] = choice_set['Przedmiot'].astype(str).str[12:] + ' - ' + choice_set['Forma'].astype(str) + ' gr. ' + choice_set['Numer grupy'].astype(str)
    gcal['Start Time'] = choice_set['Poczatek'].astype(str)
    gcal['End Time'] = choice_set['Koniec']
    gcal['Location'] = choice_set['Budynek i sala']
    gcal['Daty'] = choice_set['Daty zajęć (dd-mm-rr)']
    gcal['Grupa'] = choice_set['Numer grupy']
    gcal = (
        gcal.set_index( gcal.columns.drop('Daty', 1).tolist())
        .Daty.str.split(';', expand = True)
        .stack()
        .reset_index()
        .rename( columns = {0: 'Daty'})
        .loc[:, gcal.columns]
    )
    gcal = gcal[ gcal['Daty'] != '']
    gcal['Start Date'] = gcal['Daty'].str[3:5] + '/' + gcal['Daty'].str[0:2] + '/' + gcal['Daty'].str[6:9]
    gcal['End Date'] = gcal['Start Date']
    gcal = gcal.drop( columns = ['Daty', 'Grupa'])
    gcal['Start Time'] = pd.to_datetime( gcal['Start Time']).dt.strftime('%I:%M %p')
    gcal['End Time'] = pd.to_datetime( gcal['End Time']).dt.strftime('%I:%M %p')
    return gcal

@app.route( '/')
def hello():
    spis = np.array( smmd)
    return render_template( 'index.html', data_array=spis, filename=SMMD, dataframe=smmd)

@app.route( '/export', methods=['POST'])
def export():
    if request.method == 'POST':
        rows = request.form.getlist( 'rows[]')
        if rows:
            rows = [ int(x) for x in rows]
            gcal = convert( smmd, rows).to_csv( index=False)
            return Response(
                gcal,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=harmonogram.csv"}
            )
        else:
            return Response('Wybór był pusty!', status=406)

if __name__ == '__main__':
    app.run( debug = False)