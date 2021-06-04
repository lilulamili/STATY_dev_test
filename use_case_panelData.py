#----------------------------------------------------------------------------------------------

####################
# IMPORT LIBRARIES #
####################

import streamlit as st
import pandas as pd
import numpy as np
import plotly as dd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager
import plotly.graph_objects as go
import functions as fc
import os
import altair as alt
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, mean_absolute_error, explained_variance_score, roc_auc_score, max_error, log_loss, average_precision_score, precision_recall_curve, auc, roc_curve, confusion_matrix, recall_score, precision_score, f1_score, accuracy_score, balanced_accuracy_score, cohen_kappa_score
from sklearn.model_selection import train_test_split
import scipy
import sys
import SessionState
from streamlit import caching
import platform


from linearmodels import PanelOLS
from linearmodels import RandomEffects
from linearmodels import PooledOLS

#----------------------------------------------------------------------------------------------

def app(): 

    # Clear cache
    caching.clear_cache()

    # Hide traceback in error messages (comment out for de-bugging)
    sys.tracebacklimit = 0

    # Show altair tooltip when full screen
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',unsafe_allow_html=True)

    # Working directory
    if platform.system() == "Windows":
        cwd = os.getcwd()
    if platform.system() == "Darwin":
        cwd = str(os.path.abspath(os.path.dirname(sys.argv[0])))

    #------------------------------------------------------------------------------------------

    
    #++++++++++++++++++++++++++++++++++++++++++++
    # DATA IMPORT
    
    # File upload section
    df_dec = st.sidebar.radio("Get data", ["Use example dataset", "Upload data"])

    if df_dec == "Upload data":
        #st.subheader("Upload your data")
        uploaded_data = st.sidebar.file_uploader("", type=["csv", "txt"])
        if uploaded_data is not None:
            df = pd.read_csv(uploaded_data, sep = ";|,|\t",engine='python')
            st.sidebar.success('Loading data... done!')
        elif uploaded_data is None:
            if platform.system() == "Windows":
                cwd = os.getcwd()
                df = pd.read_csv(cwd + "\\default data\\Grunfeld.csv", sep = ";|,|\t",engine='python')
            if platform.system() == "Darwin":
                cwd = str(os.path.abspath(os.path.dirname(sys.argv[0])))
                df = pd.read_csv(cwd + "/default data/Grunfeld.csv", sep = ";|,|\t",engine='python')
    else:
        if platform.system() == "Windows":
            cwd = os.getcwd()
            df = pd.read_csv(cwd + "\\default data\\Grunfeld.csv", sep = ";|,|\t",engine='python')
        if platform.system() == "Darwin":
            cwd = str(os.path.abspath(os.path.dirname(sys.argv[0])))
            df = pd.read_csv(cwd + "/default data/Grunfeld.csv", sep = ";|,|\t",engine='python')
    st.sidebar.markdown("")
    
    #Basic data info
    n_rows = df.shape[0]
    n_cols = df.shape[1] 

    #++++++++++++++++++++++++++++++++++++++++++++
    # SETTINGS

    settings_expander=st.sidebar.beta_expander('Settings')
    with settings_expander:
        st.caption("**Help**")
        sett_hints = st.checkbox('Show learning hints', value=False)
        st.caption("**Appearance**")
        sett_wide_mode = st.checkbox('Wide mode', value=False)
        sett_theme = st.selectbox('Theme', ["Light", "Dark"])
        #sett_info = st.checkbox('Show methods info', value=False)
        #sett_prec = st.number_input('Set the number of diggits for the output', min_value=0, max_value=8, value=2)
    st.sidebar.markdown("")

    # Check if wide mode
    if sett_wide_mode:
        fc.wide_mode_func()

    # Check theme
    if sett_theme == "Dark":
        fc.theme_func_dark()
    if sett_theme == "Light":
        fc.theme_func_light()

    #++++++++++++++++++++++++++++++++++++++++++++
    # RESET INPUT

    reset_clicked = st.sidebar.button("Reset all your input")
    session_state = SessionState.get(id = 0)
    if reset_clicked:
        session_state.id = session_state.id + 1
    st.sidebar.markdown("")

    #------------------------------------------------------------------------------------------

    #++++++++++++++++++++++++++++++++++++++++++++
    # DATA EXPLORATION & VISUALIZATION
    
    st.header("**Panel data**")
    st.markdown("Get your data ready for powerfull methods! Let STATY do the data cleaning, variable transformations, visualizations and deliver you the stats you need. Specify your data processing preferences and start exploring your data stories right below... ")

    # Check if enough data is available
    if n_cols >= 2 and n_rows > 0:
        st.empty()
    else:
        st.error("ERROR: Not enough data!")
        return

    # Specifiy entity and time
    st.markdown("**Panel data specification**")
    col1, col2 = st.beta_columns(2)
    with col1:
        entity_na_warn = False
        entity_options = df.columns
        entity = st.selectbox("Select variable for entity", entity_options, key = session_state.id)
    with col2:
        time_na_warn = False
        time_options = df.columns 
        time_options = list(time_options[time_options.isin(df.drop(entity, axis = 1).columns)])
        time = st.selectbox("Select variable for time", time_options, key = session_state.id)
        
    if np.where(df[entity].isnull())[0].size > 0:
        entity_na_warn = "ERROR: The variable selected for entity has NAs!"
        st.error(entity_na_warn)
    if np.where(df[time].isnull())[0].size > 0:
        time_na_warn = "ERROR: The variable selected for time has NAs!"
        st.error(time_na_warn)
    if df[time].dtypes != "float64" and df[time].dtypes != "float32" and df[time].dtypes != "int64" and df[time].dtypes != "int32":
        time_na_warn = "ERROR: Time variable must be numeric!"
        st.error(time_na_warn)
    

    run_models = False
    if time_na_warn == False and entity_na_warn == False:

        data_empty_container = st.beta_container()
        with data_empty_container:
            st.empty()
            st.empty()
            st.empty()
            st.empty()
            st.empty()
            st.empty()
            st.empty()
            st.empty()

        # Make sure time is numeric
        df[time] = pd.to_numeric(df[time])

        data_exploration_container2 = st.beta_container()
        with data_exploration_container2:

            st.header("**Data exploration**")

            #------------------------------------------------------------------------------------------

            #++++++++++++++++++++++
            # DATA SUMMARY

            # Main panel for data summary (pre)
            #----------------------------------

            #st.subheader("Raw data exploration")
            dev_expander_dsPre = st.beta_expander("Explore raw panel data", expanded = False)
            st.empty()
            with dev_expander_dsPre:
                # Show raw data & data info
                df_summary = fc.data_summary(df) 
                if st.checkbox("Show raw data", value = False, key = session_state.id):      
                    st.write(df)
                    #st.info("Data shape: "+ str(n_rows) + " rows and " + str(n_cols) + " columns")
                    st.write("Data shape: ", n_rows,  " rows and ", n_cols, " columns")
                if df[df.duplicated()].shape[0] > 0 or df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] > 0:
                    check_nasAnddupl=st.checkbox("Show duplicates and NAs info", value = False, key = session_state.id) 
                    if check_nasAnddupl:      
                        if df[df.duplicated()].shape[0] > 0:
                            st.write("Number of duplicates: ", df[df.duplicated()].shape[0])
                            st.write("Duplicate row index: ", ', '.join(map(str,list(df.index[df.duplicated()]))))
                        if df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] > 0:
                            st.write("Number of rows with NAs: ", df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0])
                            st.write("Rows with NAs: ", ', '.join(map(str,list(pd.unique(np.where(df.isnull())[0])))))
                    
                # Show variable info 
                if st.checkbox('Show variable info', value = False, key = session_state.id): 
                    st.write(df_summary["Variable types"])
            
                # Show summary statistics (raw data)
                if st.checkbox('Show summary statistics (raw data)', value = False, key = session_state.id): 
                    st.write(df_summary["ALL"])
                    if fc.get_mode(df).loc["n_unique"].any():
                        st.caption("** Mode is not unique.")
                    if sett_hints:
                        st.info(str(fc.learning_hints("de_summary_statistics")))

            dev_expander_anovPre = st.beta_expander("Explore ANOVA for raw panel data", expanded = False)
            with dev_expander_anovPre:  
                if df.shape[1] > 2:
                    # Target variable
                    target_var = st.selectbox('Select target variable ', df.drop([entity, time], axis = 1).columns, key = session_state.id)
                    
                    if df[target_var].dtypes == "int64" or df[target_var].dtypes == "float64": 
                        class_var_options = df.columns
                        class_var_options = class_var_options[class_var_options.isin(df.drop(target_var, axis = 1).columns)]
                        clas_var = st.selectbox('Select classifier variable ', [entity, time], key = session_state.id) 

                        # Means by entity and time
                        col1, col2 = st.beta_columns(2) 
                        with col1:
                            df_anova_woTime = df.drop([time], axis = 1)
                            df_grouped_ent = df_anova_woTime.groupby(entity)
                            st.write("Mean based on entity:")
                            st.write(df_grouped_ent.mean()[target_var])
                            st.write("")
                        with col2:
                            st.write("SD based on entity:")
                            st.write(df_grouped_ent.std()[target_var])
                            st.write("")

                        # SD by entity and time
                        col3, col4 = st.beta_columns(2) 
                        with col3:
                            df_anova_woEnt= df.drop([entity], axis = 1)
                            df_grouped_time = df_anova_woEnt.groupby(time)
                            counts_time = pd.DataFrame(df_grouped_time.count()[target_var])
                            counts_time.columns = ["count"]
                            st.write("Mean based on time:")
                            st.write(df_grouped_time.mean()[target_var])
                            st.write("")
                        with col4:
                            st.write("SD based on time:")
                            st.write(df_grouped_time.std()[target_var])
                            st.write("")

                        col9, col10 = st.beta_columns(2) 
                        with col9:
                            st.write("Boxplot grouped by entity:")
                            box_size1 = st.slider("Select box size", 1, 50, 5, key = session_state.id)
                            # Grouped boxplot by entity
                            grouped_boxplot_data = pd.DataFrame()
                            grouped_boxplot_data[entity] = df[entity]
                            grouped_boxplot_data[time] = df[time]
                            grouped_boxplot_data["Index"] = df.index
                            grouped_boxplot_data[target_var] = df[target_var]
                            grouped_boxchart_ent = alt.Chart(grouped_boxplot_data, height = 300).mark_boxplot(size = box_size1, color = "#1f77b4", median = dict(color = "darkred")).encode(
                                x = alt.X(entity, scale = alt.Scale(zero = False)),
                                y = alt.Y(target_var, scale = alt.Scale(zero = False)), 
                                tooltip = [target_var, entity, time, "Index"]
                            ).configure_axis(
                                labelFontSize = 11,
                                titleFontSize = 12
                            )
                            st.altair_chart(grouped_boxchart_ent, use_container_width=True)
                        with col10:
                            st.write("Boxplot grouped by time:")
                            box_size2 = st.slider("Select box size ", 1, 50, 5, key = session_state.id)
                            # Grouped boxplot by time
                            grouped_boxplot_data = pd.DataFrame()
                            grouped_boxplot_data[entity] = df[entity]
                            grouped_boxplot_data[time] = df[time]
                            grouped_boxplot_data["Index"] = df.index
                            grouped_boxplot_data[target_var] = df[target_var]
                            grouped_boxchart_time = alt.Chart(grouped_boxplot_data, height = 300).mark_boxplot(size = box_size2, color = "#1f77b4", median = dict(color = "darkred")).encode(
                                x = alt.X(time, scale = alt.Scale(domain = [min(df[time]), max(df[time])])),
                                y = alt.Y(target_var, scale = alt.Scale(zero = False)),
                                tooltip = [target_var, entity, time, "Index"]
                            ).configure_axis(
                                labelFontSize = 11,
                                titleFontSize = 12
                            )
                            st.altair_chart(grouped_boxchart_time, use_container_width=True)
                        if sett_hints:
                            st.info(str(fc.learning_hints("de_anova_boxplot")))
                        st.write("")
                        
                        # Count for entity and time
                        col5, col6 = st.beta_columns(2)
                        with col5:
                            st.write("Number of observations per entity:")
                            counts_ent = pd.DataFrame(df_grouped_ent.count()[target_var])
                            counts_ent.columns = ["count"]
                            st.write(counts_ent.transpose())
                        with col6:
                            st.write("Number of observations per time:")
                            counts_time = pd.DataFrame(df_grouped_time.count()[target_var])
                            counts_time.columns = ["count"]
                            st.write(counts_time.transpose())  
                        if sett_hints:
                            st.info(str(fc.learning_hints("de_anova_count")))
                        st.write("")
                        
                        # ANOVA calculation
                        df_grouped = df[[target_var,clas_var]].groupby(clas_var)
                        overall_mean = (df_grouped.mean()*df_grouped.count()).sum()/df_grouped.count().sum()
                        dof_between = len(df_grouped.count())-1
                        dof_within = df_grouped.count().sum()-len(df_grouped.count())
                        dof_tot = dof_between + dof_within

                        SS_between = (((df_grouped.mean()-overall_mean)**2)*df_grouped.count()).sum()
                        SS_within =  (df_grouped.var()*(df_grouped.count()-1)).sum()
                        SS_total = SS_between + SS_within

                        MS_between = SS_between/dof_between
                        MS_within = SS_within/dof_within
                        F_stat = MS_between/MS_within
                        p_value = scipy.stats.f.sf(F_stat, dof_between, dof_within)

                        anova_table=pd.DataFrame({
                            "DF": [dof_between, dof_within.values[0], dof_tot.values[0]],
                            "SS": [SS_between.values[0], SS_within.values[0], SS_total.values[0]],
                            "MS": [MS_between.values[0], MS_within.values[0], ""],
                            "F-statistic": [F_stat.values[0], "", ""],
                            "p-value": [p_value[0], "", ""]},
                            index = ["Between", "Within", "Total"],)
                        
                        st.write("ANOVA:")
                        st.write(anova_table)
                        if sett_hints:
                            st.info(str(fc.learning_hints("de_anova_table")))    
                        st.write("")

                        #Anova (OLS)
                        codes = pd.factorize(df[clas_var])[0]
                        ano_ols = sm.OLS(df[target_var], sm.add_constant(codes))
                        ano_ols_output = ano_ols.fit()
                        residuals = ano_ols_output.resid
                    
                        col7, col8 = st.beta_columns(2)
                        with col7:
                            # QQ-plot
                            st.write("Normal QQ-plot:")
                            st.write("")
                            st.write("")
                            st.write("")
                            st.write("")
                            st.write("")
                            st.write("")
                            qq_plot_data = pd.DataFrame()
                            qq_plot_data["StandResiduals"] = (residuals - residuals.mean())/residuals.std()
                            qq_plot_data["Index"] = df.index
                            qq_plot_data[entity] = df[entity]
                            qq_plot_data[time] = df[time]
                            qq_plot_data = qq_plot_data.sort_values(by = ["StandResiduals"])
                            qq_plot_data["Theoretical quantiles"] = stats.probplot(residuals, dist="norm")[0][0]
                            qq_plot = alt.Chart(qq_plot_data, height = 300).mark_circle(size=20).encode(
                                x = alt.X("Theoretical quantiles", title = "theoretical quantiles", scale = alt.Scale(domain = [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                y = alt.Y("StandResiduals", title = "stand. residuals", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                tooltip = ["StandResiduals", "Theoretical quantiles", entity, time, "Index"]
                            )
                            line = alt.Chart(
                                pd.DataFrame({"Theoretical quantiles": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])], "StandResiduals": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]})).mark_line(size = 2, color = "darkred").encode(
                                        alt.X("Theoretical quantiles"),
                                        alt.Y("StandResiduals"),
                            )
                            st.altair_chart(qq_plot + line, use_container_width = True)
                        with col8:
                            # Residuals histogram
                            st.write("Residuals histogram:")
                            residuals_hist = pd.DataFrame(residuals)
                            residuals_hist.columns = ["residuals"]
                            binNo_res = st.slider("Select maximum number of bins ", 5, 100, 25, key = session_state.id)
                            hist_plot_res = alt.Chart(residuals_hist, height = 300).mark_bar().encode(
                                x = alt.X("residuals", title = "residuals", bin = alt.BinParams(maxbins = binNo_res), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                y = alt.Y("count()", title = "count of records", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                tooltip = ["count()", alt.Tooltip("residuals", bin = alt.BinParams(maxbins = binNo_res))]
                            ) 
                            st.altair_chart(hist_plot_res, use_container_width=True)
                        if sett_hints:
                            st.info(str(fc.learning_hints("de_anova_residuals"))) 
                        st.write("")

                    else:
                        st.error("ERROR: The target variable must be a numerical one!")
                else: st.error("ERROR: No variables available for ANOVA!")

            #++++++++++++++++++++++
            # DATA PROCESSING

            # Settings for data processing
            #-------------------------------------
            
            dev_expander_dm_sb = st.beta_expander("Specify data processing preferences", expanded = False)
            with dev_expander_dm_sb:
                
                n_rows_wNAs = df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0]
                if n_rows_wNAs > 0:
                    a1, a2, a3 = st.beta_columns(3)
                else: a1, a2 = st.beta_columns(2)

                sb_DM_dImp_num = None 
                sb_DM_dImp_other = None
                group_by_num = None
                group_by_other = None
                if n_rows_wNAs > 0:
                    with a1:
                        #--------------------------------------------------------------------------------------
                        # DATA CLEANING

                        st.markdown("**Data cleaning**")

                        # Delete duplicates if any exist
                        if df[df.duplicated()].shape[0] > 0:
                            sb_DM_delDup = st.selectbox("Delete duplicate rows", ["No", "Yes"], key = session_state.id)
                            if sb_DM_delDup == "Yes":
                                n_rows_dup = df[df.duplicated()].shape[0]
                                df = df.drop_duplicates()
                        elif df[df.duplicated()].shape[0] == 0:   
                            sb_DM_delDup = "No"    
                            
                        # Delete rows with NA if any exist
                        n_rows_wNAs = df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0]
                        if n_rows_wNAs > 0:
                            sb_DM_delRows_wNA = st.selectbox("Delete rows with NAs", ["No", "Yes"], key = session_state.id)
                            if sb_DM_delRows_wNA == "Yes": 
                                df = df.dropna()
                        elif n_rows_wNAs == 0: 
                            sb_DM_delRows_wNA = "No"   

                        # Delete rows
                        sb_DM_delRows = st.multiselect("Select rows to delete", df.index, key = session_state.id)
                        df = df.loc[~df.index.isin(sb_DM_delRows)]

                        # Delete columns
                        sb_DM_delCols = st.multiselect("Select columns to delete", df.drop([entity, time], axis = 1).columns, key = session_state.id)
                        df = df.loc[:,~df.columns.isin(sb_DM_delCols)]
                
                    with a2:
                        #--------------------------------------------------------------------------------------
                        # DATA IMPUTATION

                        # Select data imputation method (only if rows with NA not deleted)
                        if sb_DM_delRows_wNA == "No" and n_rows_wNAs > 0:
                            st.markdown("**Data imputation**")
                            sb_DM_dImp_choice = st.selectbox("Replace entries with NA", ["No", "Yes"], key = session_state.id)
                            if sb_DM_dImp_choice == "Yes":
                                # Numeric variables
                                sb_DM_dImp_num = st.selectbox("Imputation method for numeric variables", ["Mean", "Median", "Random value"], key = session_state.id)
                                # Other variables
                                sb_DM_dImp_other = st.selectbox("Imputation method for other variables", ["Mode", "Random value"], key = session_state.id)
                                group_by_num = st.selectbox("Group imputation by", ["None", "Entity", "Time"], key = session_state.id)
                                group_by_other = group_by_num
                                df = fc.data_impute_panel(df, sb_DM_dImp_num, sb_DM_dImp_other, group_by_num, group_by_other, entity, time)
                        else: 
                            st.markdown("**Data imputation**")
                            st.write("")
                            st.info("No NAs in data set!")
                    with a3:
                        #--------------------------------------------------------------------------------------
                        # DATA TRANSFORMATION

                        st.markdown("**Data transformation**")
                        # Select columns for different transformation types
                        transform_options = df.drop([entity, time], axis = 1).select_dtypes([np.number]).columns
                        numCat_options = df.drop([entity, time], axis = 1).columns
                        sb_DM_dTrans_log = st.multiselect("Select columns to transform with log", transform_options, key = session_state.id)
                        if sb_DM_dTrans_log is not None: 
                            df = fc.var_transform_log(df, sb_DM_dTrans_log)
                        sb_DM_dTrans_sqrt = st.multiselect("Select columns to transform with sqrt", transform_options, key = session_state.id)
                        if sb_DM_dTrans_sqrt is not None: 
                            df = fc.var_transform_sqrt(df, sb_DM_dTrans_sqrt)
                        sb_DM_dTrans_square = st.multiselect("Select columns for squaring", transform_options, key = session_state.id)
                        if sb_DM_dTrans_square is not None: 
                            df = fc.var_transform_square(df, sb_DM_dTrans_square)
                        sb_DM_dTrans_stand = st.multiselect("Select columns for standardization", transform_options, key = session_state.id)
                        if sb_DM_dTrans_stand is not None: 
                            df = fc.var_transform_stand(df, sb_DM_dTrans_stand)
                        sb_DM_dTrans_norm = st.multiselect("Select columns for normalization", transform_options, key = session_state.id)
                        if sb_DM_dTrans_norm is not None: 
                            df = fc.var_transform_norm(df, sb_DM_dTrans_norm)
                        if df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] == 0:
                            sb_DM_dTrans_numCat = st.multiselect("Select columns for numeric categorization", numCat_options, key = session_state.id)
                            if sb_DM_dTrans_numCat is not None: 
                                df = fc.var_transform_numCat(df, sb_DM_dTrans_numCat)
                        else:
                            sb_DM_dTrans_numCat = None
                else:
                    with a1:
                        #--------------------------------------------------------------------------------------
                        # DATA CLEANING

                        st.markdown("**Data cleaning**")

                        # Delete duplicates if any exist
                        if df[df.duplicated()].shape[0] > 0:
                            sb_DM_delDup = st.selectbox("Delete duplicate rows", ["No", "Yes"], key = session_state.id)
                            if sb_DM_delDup == "Yes":
                                n_rows_dup = df[df.duplicated()].shape[0]
                                df = df.drop_duplicates()
                        elif df[df.duplicated()].shape[0] == 0:   
                            sb_DM_delDup = "No"    
                            
                        # Delete rows with NA if any exist
                        n_rows_wNAs = df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0]
                        if n_rows_wNAs > 0:
                            sb_DM_delRows_wNA = st.selectbox("Delete rows with NAs", ["No", "Yes"], key = session_state.id)
                            if sb_DM_delRows_wNA == "Yes": 
                                df = df.dropna()
                        elif n_rows_wNAs == 0: 
                            sb_DM_delRows_wNA = "No"   

                        # Delete rows
                        sb_DM_delRows = st.multiselect("Select rows to delete", df.index, key = session_state.id)
                        df = df.loc[~df.index.isin(sb_DM_delRows)]

                        # Delete columns
                        sb_DM_delCols = st.multiselect("Select columns to delete", df.drop([entity, time], axis = 1).columns, key = session_state.id)
                        df = df.loc[:,~df.columns.isin(sb_DM_delCols)]

                    with a2:
                        #--------------------------------------------------------------------------------------
                        # DATA TRANSFORMATION

                        st.markdown("**Data transformation**")
                        # Select columns for different transformation types
                        transform_options = df.drop([entity, time], axis = 1).select_dtypes([np.number]).columns
                        numCat_options = df.drop([entity, time], axis = 1).columns
                        sb_DM_dTrans_log = st.multiselect("Select columns to transform with log", transform_options, key = session_state.id)
                        if sb_DM_dTrans_log is not None: 
                            df = fc.var_transform_log(df, sb_DM_dTrans_log)
                        sb_DM_dTrans_sqrt = st.multiselect("Select columns to transform with sqrt", transform_options, key = session_state.id)
                        if sb_DM_dTrans_sqrt is not None: 
                            df = fc.var_transform_sqrt(df, sb_DM_dTrans_sqrt)
                        sb_DM_dTrans_square = st.multiselect("Select columns for squaring", transform_options, key = session_state.id)
                        if sb_DM_dTrans_square is not None: 
                            df = fc.var_transform_square(df, sb_DM_dTrans_square)
                        sb_DM_dTrans_stand = st.multiselect("Select columns for standardization", transform_options, key = session_state.id)
                        if sb_DM_dTrans_stand is not None: 
                            df = fc.var_transform_stand(df, sb_DM_dTrans_stand)
                        sb_DM_dTrans_norm = st.multiselect("Select columns for normalization", transform_options, key = session_state.id)
                        if sb_DM_dTrans_norm is not None: 
                            df = fc.var_transform_norm(df, sb_DM_dTrans_norm)
                        if df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] == 0:
                            sb_DM_dTrans_numCat = st.multiselect("Select columns for numeric categorization", numCat_options, key = session_state.id)
                            if sb_DM_dTrans_numCat is not None: 
                                df = fc.var_transform_numCat(df, sb_DM_dTrans_numCat)
                        else:
                            sb_DM_dTrans_numCat = None

                #--------------------------------------------------------------------------------------
                # PROCESSING SUMMARY

                if st.checkbox('Show a summary of my data processing preferences', value = False, key = session_state.id): 
                    st.markdown("Summary of data changes:")
                    
                    #--------------------------------------------------------------------------------------
                    # DATA CLEANING

                    # Duplicates
                    if sb_DM_delDup == "Yes":
                        if n_rows_dup > 1:
                            st.write("-", n_rows_dup, " duplicate rows were deleted!")
                        elif n_rows_dup == 1:
                            st.write("-", n_rows_dup, "duplicate row was deleted!")
                    else:
                        st.write("- No duplicate row was deleted!")
                    # NAs
                    if sb_DM_delRows_wNA == "Yes":
                        if n_rows_wNAs > 1:
                            st.write("-", n_rows_wNAs, "rows with NAs were deleted!")
                        elif n_rows_wNAs == 1:
                            st.write("-", n_rows - n_rows_wNAs, "row with NAs was deleted!")
                    else:
                        st.write("- No row with NAs was deleted!")
                    # Rows
                    if len(sb_DM_delRows) > 1:
                        st.write("-", len(sb_DM_delRows), " rows were manually deleted:", ', '.join(map(str,sb_DM_delRows)))
                    elif len(sb_DM_delRows) == 1:
                        st.write("-",len(sb_DM_delRows), " row was manually deleted:", str(sb_DM_delRows[0]))
                    elif len(sb_DM_delRows) == 0:
                        st.write("- No row was manually deleted!")
                    # Columns
                    if len(sb_DM_delCols) > 1:
                        st.write("-", len(sb_DM_delCols), " columns were manually deleted:", ', '.join(sb_DM_delCols))
                    elif len(sb_DM_delCols) == 1:
                        st.write("-",len(sb_DM_delCols), " column was manually deleted:", str(sb_DM_delCols[0]))
                    elif len(sb_DM_delCols) == 0:
                        st.write("- No column was manually deleted!")
                    
                    #--------------------------------------------------------------------------------------
                    # DATA IMPUTATION

                    if sb_DM_delRows_wNA == "No" and n_rows_wNAs > 0:
                        st.write("- Data imputation method for numeric variables:", sb_DM_dImp_num)
                        st.write("- Data imputation method for other variable types:", sb_DM_dImp_other)
                        st.write("- Imputation grouped by:", group_by_num)

                    #--------------------------------------------------------------------------------------
                    # DATA TRANSFORMATION

                    # log
                    if len(sb_DM_dTrans_log) > 1:
                        st.write("-", len(sb_DM_dTrans_log), " columns were log-transformed:", ', '.join(sb_DM_dTrans_log))
                    elif len(sb_DM_dTrans_log) == 1:
                        st.write("-",len(sb_DM_dTrans_log), " column was log-transformed:", sb_DM_dTrans_log[0])
                    elif len(sb_DM_dTrans_log) == 0:
                        st.write("- No column was log-transformed!")
                    # sqrt
                    if len(sb_DM_dTrans_sqrt) > 1:
                        st.write("-", len(sb_DM_dTrans_sqrt), " columns were sqrt-transformed:", ', '.join(sb_DM_dTrans_sqrt))
                    elif len(sb_DM_dTrans_sqrt) == 1:
                        st.write("-",len(sb_DM_dTrans_sqrt), " column was sqrt-transformed:", sb_DM_dTrans_sqrt[0])
                    elif len(sb_DM_dTrans_sqrt) == 0:
                        st.write("- No column was sqrt-transformed!")
                    # square
                    if len(sb_DM_dTrans_square) > 1:
                        st.write("-", len(sb_DM_dTrans_square), " columns were squared:", ', '.join(sb_DM_dTrans_square))
                    elif len(sb_DM_dTrans_square) == 1:
                        st.write("-",len(sb_DM_dTrans_square), " column was squared:", sb_DM_dTrans_square[0])
                    elif len(sb_DM_dTrans_square) == 0:
                        st.write("- No column was squared!")
                    # standardize
                    if len(sb_DM_dTrans_stand) > 1:
                        st.write("-", len(sb_DM_dTrans_stand), " columns were standardized:", ', '.join(sb_DM_dTrans_stand))
                    elif len(sb_DM_dTrans_stand) == 1:
                        st.write("-",len(sb_DM_dTrans_stand), " column was standardized:", sb_DM_dTrans_stand[0])
                    elif len(sb_DM_dTrans_stand) == 0:
                        st.write("- No column was standardized!")
                    # normalize
                    if len(sb_DM_dTrans_norm) > 1:
                        st.write("-", len(sb_DM_dTrans_norm), " columns were normalized:", ', '.join(sb_DM_dTrans_norm))
                    elif len(sb_DM_dTrans_norm) == 1:
                        st.write("-",len(sb_DM_dTrans_norm), " column was normalized:", sb_DM_dTrans_norm[0])
                    elif len(sb_DM_dTrans_norm) == 0:
                        st.write("- No column was normalized!")
                    # numeric category
                    if df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] == 0:
                        if len(sb_DM_dTrans_numCat) > 1:
                            st.write("-", len(sb_DM_dTrans_numCat), " columns were transformed to numeric categories:", ', '.join(sb_DM_dTrans_numCat))
                        elif len(sb_DM_dTrans_numCat) == 1:
                            st.write("-",len(sb_DM_dTrans_numCat), " column was transformed to numeric categories:", sb_DM_dTrans_numCat[0])
                        elif len(sb_DM_dTrans_numCat) == 0:
                            st.write("- No column was transformed to numeric categories!")
            
            #------------------------------------------------------------------------------------------
            
            #++++++++++++++++++++++
            # UPDATED DATA SUMMARY   

            # Show only if changes were made
            if  any(v for v in [sb_DM_delRows, sb_DM_delCols, sb_DM_dImp_num, sb_DM_dImp_other, sb_DM_dTrans_log, sb_DM_dTrans_sqrt, sb_DM_dTrans_square, sb_DM_dTrans_stand, sb_DM_dTrans_norm, sb_DM_dTrans_numCat ] if v is not None) or sb_DM_delDup == "Yes" or sb_DM_delRows_wNA == "Yes":
                dev_expander_dsPost = st.beta_expander("Explore cleaned and transformed panel data", expanded = False)
                with dev_expander_dsPost:
                    if df.shape[1] > 2 and df.shape[0] > 0:

                        # Show cleaned and transformed data & data info
                        df_summary_post = fc.data_summary(df)
                        if st.checkbox("Show cleaned and transformed data", value = False):  
                            n_rows_post = df.shape[0]
                            n_cols_post = df.shape[1]
                            st.dataframe(df)
                            st.write("Data shape: ", n_rows_post, "rows and ", n_cols_post, "columns")
                        if df[df.duplicated()].shape[0] > 0 or df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] > 0:
                            check_nasAnddupl2 = st.checkbox("Show duplicates and NAs info (processed)", value = False) 
                            if check_nasAnddupl2:
                                index_c = []
                                for c in df.columns:
                                    for r in df.index:
                                        if pd.isnull(df[c][r]):
                                            index_c.append(r)      
                                if df[df.duplicated()].shape[0] > 0:
                                    st.write("Number of duplicates: ", df[df.duplicated()].shape[0])
                                    st.write("Duplicate row index: ", ', '.join(map(str,list(df.index[df.duplicated()]))))
                                if df.iloc[list(pd.unique(np.where(df.isnull())[0]))].shape[0] > 0:
                                    st.write("Number of rows with NAs: ", len(pd.unique(sorted(index_c))))
                                    st.write("Rows with NAs: ", ', '.join(map(str,list(pd.unique(sorted(index_c))))))

                        # Show cleaned and transformed variable info
                        if st.checkbox("Show cleaned and transformed variable info", value = False): 
                            st.write(df_summary_post["Variable types"])

                        # Show summary statistics (cleaned and transformed data)
                        if st.checkbox('Show summary statistics (cleaned and transformed data)', value = False):
                            st.write(df_summary_post["ALL"])
                            if fc.get_mode(df).loc["n_unique"].any():
                                st.caption("** Mode is not unique.") 
                            if sett_hints:
                                st.info(str(fc.learning_hints("de_summary_statistics")))
                    else: st.error("ERROR: No data available for Data Exploration!") 

                dev_expander_anovPost = st.beta_expander("Explore ANOVA for cleaned and transformed panel data", expanded = False)
                with dev_expander_anovPost:
                    if df.shape[1] > 2 and df.shape[0] > 0:
                        
                        # Target variable
                        target_var2 = st.selectbox('Select target variable', df.drop([entity, time], axis = 1).columns)
                        
                        if df[target_var2].dtypes == "int64" or df[target_var2].dtypes == "float64": 
                            class_var_options = df.columns
                            class_var_options = class_var_options[class_var_options.isin(df.drop(target_var2, axis = 1).columns)]
                            clas_var2 = st.selectbox('Select classifier variable', [entity, time],) 

                            # Means by entity and time
                            col1, col2 = st.beta_columns(2) 
                            with col1:
                                df_anova_woTime = df.drop([time], axis = 1)
                                df_grouped_ent = df_anova_woTime.groupby(entity)
                                st.write("Mean based on entity:")
                                st.write(df_grouped_ent.mean()[target_var2])
                                st.write("")
                            with col2:
                                st.write("SD based on entity:")
                                st.write(df_grouped_ent.std()[target_var2])
                                st.write("")

                            # SD by entity and time
                            col3, col4 = st.beta_columns(2) 
                            with col3:
                                df_anova_woEnt= df.drop([entity], axis = 1)
                                df_grouped_time = df_anova_woEnt.groupby(time)
                                counts_time = pd.DataFrame(df_grouped_time.count()[target_var2])
                                counts_time.columns = ["count"]
                                st.write("Mean based on time:")
                                st.write(df_grouped_time.mean()[target_var2])
                                st.write("")
                            with col4:
                                st.write("SD based on time:")
                                st.write(df_grouped_time.std()[target_var2])
                                st.write("")

                            col9, col10 = st.beta_columns(2) 
                            with col9:
                                st.write("Boxplot grouped by entity:")
                                box_size1 = st.slider("Select box size  ", 1, 50, 5)
                                # Grouped boxplot by entity
                                grouped_boxplot_data = pd.DataFrame()
                                grouped_boxplot_data[entity] = df[entity]
                                grouped_boxplot_data[time] = df[time]
                                grouped_boxplot_data["Index"] = df.index
                                grouped_boxplot_data[target_var2] = df[target_var2]
                                grouped_boxchart_ent = alt.Chart(grouped_boxplot_data, height = 300).mark_boxplot(size = box_size1, color = "#1f77b4", median = dict(color = "darkred")).encode(
                                    x = alt.X(entity, scale = alt.Scale(zero = False)),
                                    y = alt.Y(target_var2, scale = alt.Scale(zero = False)),
                                    tooltip = [target_var2, entity, time, "Index"]
                                ).configure_axis(
                                    labelFontSize = 11,
                                    titleFontSize = 12
                                )
                                st.altair_chart(grouped_boxchart_ent, use_container_width=True)
                            with col10:
                                st.write("Boxplot grouped by time:")
                                box_size2 = st.slider("Select box size   ", 1, 50, 5)
                                # Grouped boxplot by time
                                grouped_boxplot_data = pd.DataFrame()
                                grouped_boxplot_data[time] = df[time]
                                grouped_boxplot_data[entity] = df[entity]
                                grouped_boxplot_data["Index"] = df.index
                                grouped_boxplot_data[target_var2] = df[target_var2]
                                grouped_boxchart_time = alt.Chart(grouped_boxplot_data, height = 300).mark_boxplot(size = box_size2, color = "#1f77b4", median = dict(color = "darkred")).encode(
                                    x = alt.X(time, scale = alt.Scale(domain = [min(df[time]), max(df[time])])),
                                    y = alt.Y(target_var2, scale = alt.Scale(zero = False)),
                                    tooltip = [target_var2, entity, time, "Index"]
                                ).configure_axis(
                                    labelFontSize = 11,
                                    titleFontSize = 12
                                )
                                st.altair_chart(grouped_boxchart_time, use_container_width=True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("de_anova_boxplot")))
                            st.write("")
                            
                            # Count for entity and time
                            col5, col6 = st.beta_columns(2)
                            with col5:
                                st.write("Number of observations per entity:")
                                counts_ent = pd.DataFrame(df_grouped_ent.count()[target_var2])
                                counts_ent.columns = ["count"]
                                st.write(counts_ent.transpose())
                            with col6:
                                st.write("Number of observations per time:")
                                counts_time = pd.DataFrame(df_grouped_time.count()[target_var2])
                                counts_time.columns = ["count"]
                                st.write(counts_time.transpose()) 
                            if sett_hints:
                                st.info(str(fc.learning_hints("de_anova_count")))
                            st.write("")
                            
                            # ANOVA calculation
                            df_grouped = df[[target_var2,clas_var2]].groupby(clas_var2)
                            overall_mean = (df_grouped.mean()*df_grouped.count()).sum()/df_grouped.count().sum()
                            dof_between = len(df_grouped.count())-1
                            dof_within = df_grouped.count().sum()-len(df_grouped.count())
                            dof_tot = dof_between + dof_within

                            SS_between = (((df_grouped.mean()-overall_mean)**2)*df_grouped.count()).sum()
                            SS_within =  (df_grouped.var()*(df_grouped.count()-1)).sum()
                            SS_total = SS_between + SS_within

                            MS_between = SS_between/dof_between
                            MS_within = SS_within/dof_within
                            F_stat = MS_between/MS_within
                            p_value = scipy.stats.f.sf(F_stat, dof_between, dof_within)

                            anova_table=pd.DataFrame({
                                "DF": [dof_between, dof_within.values[0], dof_tot.values[0]],
                                "SS": [SS_between.values[0], SS_within.values[0], SS_total.values[0]],
                                "MS": [MS_between.values[0], MS_within.values[0], ""],
                                "F-statistic": [F_stat.values[0], "", ""],
                                "p-value": [p_value[0], "", ""]},
                                index = ["Between", "Within", "Total"],)
                            
                            st.write("ANOVA:")
                            st.write(anova_table)
                            if sett_hints:
                                st.info(str(fc.learning_hints("de_anova_table"))) 
                            st.write("")  

                            #Anova (OLS)
                            codes = pd.factorize(df[clas_var2])[0]
                            ano_ols = sm.OLS(df[target_var2], sm.add_constant(codes))
                            ano_ols_output = ano_ols.fit()
                            residuals = ano_ols_output.resid
                            
                            col7, col8 = st.beta_columns(2)
                            with col7:
                                # QQ-plot
                                st.write("Normal QQ-plot:")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")
                                qq_plot_data = pd.DataFrame()
                                qq_plot_data["StandResiduals"] = (residuals - residuals.mean())/residuals.std()
                                qq_plot_data["Index"] = df.index
                                qq_plot_data[entity] = df[entity]
                                qq_plot_data[time] = df[time]
                                qq_plot_data = qq_plot_data.sort_values(by = ["StandResiduals"])
                                qq_plot_data["Theoretical quantiles"] = stats.probplot(residuals, dist="norm")[0][0]
                                qq_plot = alt.Chart(qq_plot_data, height = 300).mark_circle(size=20).encode(
                                    x = alt.X("Theoretical quantiles", title = "theoretical quantiles", scale = alt.Scale(domain = [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    y = alt.Y("StandResiduals", title = "stand. residuals", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    tooltip = ["StandResiduals", "Theoretical quantiles", entity, time, "Index"]
                                )
                                line = alt.Chart(
                                    pd.DataFrame({"Theoretical quantiles": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])], "StandResiduals": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]})).mark_line(size = 2, color = "darkred").encode(
                                            alt.X("Theoretical quantiles"),
                                            alt.Y("StandResiduals"),
                                )
                                st.altair_chart(qq_plot + line, use_container_width = True)
                            with col8:
                                # Residuals histogram
                                st.write("Residuals histogram:")
                                residuals_hist = pd.DataFrame(residuals)
                                residuals_hist.columns = ["residuals"]
                                binNo_res2 = st.slider("Select maximum number of bins  ", 5, 100, 25)
                                hist_plot = alt.Chart(residuals_hist, height = 300).mark_bar().encode(
                                    x = alt.X("residuals", title = "residuals", bin = alt.BinParams(maxbins = binNo_res2), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    y = alt.Y("count()", title = "count of records", axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    tooltip = ["count()", alt.Tooltip("residuals", bin = alt.BinParams(maxbins = binNo_res2))]
                                ) 
                                st.altair_chart(hist_plot, use_container_width=True)  
                            if sett_hints:
                                st.info(str(fc.learning_hints("de_anova_residuals"))) 
                                st.write("")       
                        else:
                            st.error("ERROR: The target variable must be a numerical one!")
                    else: st.error("ERROR: No data available for ANOVA!") 
                
        #------------------------------------------------------------------------------------------
        
        #++++++++++++++++++++++
        # DATA VISUALIZATION

        data_visualization_container = st.beta_container()
        with data_visualization_container:
            #st.write("")
            st.write("")
            st.write("")
            st.header("**Data visualization**")

            #st.subheader("Graphical exploration")
            dev_expander_dv = st.beta_expander("Explore visualization types", expanded = False)
            
            with dev_expander_dv:
                if df.shape[1] > 2 and df.shape[0] > 0:
                    st.write('**Variable selection**')
                    varl_sel_options = df.columns
                    varl_sel_options = varl_sel_options[varl_sel_options.isin(df.drop([entity, time], axis = 1).columns)]
                    var_sel = st.selectbox('Select variable for visualizations', varl_sel_options, key = session_state.id)

                    if df[var_sel].dtypes == "float64" or df[var_sel].dtypes == "float32" or df[var_sel].dtypes == "int64" or df[var_sel].dtypes == "int32":
                        a4, a5 = st.beta_columns(2)
                        with a4:
                            st.write('**Scatterplot**')
                            yy_options = df.columns
                            yy_options = yy_options[yy_options.isin(df.drop([entity, time], axis = 1).columns)]
                            yy = st.selectbox('Select variable for y-axis', yy_options, key = session_state.id)
                            if df[yy].dtypes == "float64" or df[yy].dtypes == "float32" or df[yy].dtypes == "int64" or df[yy].dtypes == "int32":
                                fig_data = pd.DataFrame()
                                fig_data[yy] = df[yy]
                                fig_data[var_sel] = df[var_sel]
                                fig_data["Index"] = df.index
                                fig_data[entity] = df[entity]
                                fig_data[time] = df[time]
                                fig = alt.Chart(fig_data).mark_circle().encode(
                                    x = alt.X(var_sel, scale = alt.Scale(domain = [min(fig_data[var_sel]), max(fig_data[var_sel])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    y = alt.Y(yy, scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                    tooltip = [yy, var_sel, entity, time, "Index"]
                                )
                                st.altair_chart(fig + fig.transform_regression(var_sel, yy).mark_line(size = 2, color = "darkred"), use_container_width=True)
                                if sett_hints:
                                    st.info(str(fc.learning_hints("dv_scatterplot")))
                            else: st.error("ERROR: Please select a numeric variable for the y-axis!")   
                        with a5:
                            st.write('**Histogram**')
                            binNo = st.slider("Select maximum number of bins", 5, 100, 25, key = session_state.id)
                            fig2 = alt.Chart(df).mark_bar().encode(
                                x = alt.X(var_sel, title = var_sel + " (binned)", bin = alt.BinParams(maxbins = binNo), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                y = alt.Y("count()", title = "count of records", axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                tooltip = ["count()", alt.Tooltip(var_sel, bin = alt.BinParams(maxbins = binNo))]
                            )
                            st.altair_chart(fig2, use_container_width=True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("dv_histogram")))

                        a6, a7 = st.beta_columns(2)
                        with a6:
                            st.write('**Boxplot**')
                            # Boxplot
                            boxplot_data = pd.DataFrame()
                            boxplot_data[var_sel] = df[var_sel]
                            boxplot_data["Index"] = df.index
                            boxplot_data[entity] = df[entity]
                            boxplot_data[time] = df[time]
                            boxplot = alt.Chart(boxplot_data).mark_boxplot(size = 100, color = "#1f77b4", median = dict(color = "darkred")).encode(
                                y = alt.Y(var_sel, scale = alt.Scale(zero = False)),
                                tooltip = [var_sel, entity, time, "Index"]
                            ).configure_axis(
                                labelFontSize = 11,
                                titleFontSize = 12
                            )
                            st.altair_chart(boxplot, use_container_width=True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("dv_boxplot")))
                        with a7:
                            st.write("**QQ-plot**")
                            var_values = df[var_sel]
                            qqplot_data = pd.DataFrame()
                            qqplot_data[var_sel] = var_values
                            qqplot_data["Index"] = df.index
                            qqplot_data[entity] = df[entity]
                            qqplot_data[time] = df[time]
                            qqplot_data = qqplot_data.sort_values(by = [var_sel])
                            qqplot_data["Theoretical quantiles"] = stats.probplot(var_values, dist="norm")[0][0]
                            qqplot = alt.Chart(qqplot_data).mark_circle(size=20).encode(
                                x = alt.X("Theoretical quantiles", title = "theoretical quantiles", scale = alt.Scale(domain = [min(qqplot_data["Theoretical quantiles"]), max(qqplot_data["Theoretical quantiles"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                y = alt.Y(var_sel, title = str(var_sel), scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                                tooltip = [var_sel, "Theoretical quantiles", entity, time, "Index"]
                            )
                            st.altair_chart(qqplot + qqplot.transform_regression('Theoretical quantiles', var_sel).mark_line(size = 2, color = "darkred"), use_container_width = True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("dv_qqplot")))
                    else: st.error("ERROR: Please select a numeric variable!") 
                else: st.error("ERROR: No data available for Data Visualization!")  

            # Check again after processing
            if np.where(df[entity].isnull())[0].size > 0:
                    entity_na_warn = "WARNING: The variable selected for entity has NAs!"
            else:entity_na_warn = False
            if np.where(df[time].isnull())[0].size > 0:
                    time_na_warn = "WARNING: The variable selected for time has NAs!"
            else:time_na_warn = False

        #------------------------------------------------------------------------------------------

        #++++++++++++++++++++++++++++++++++++++++++++
        # PANEL DATA MODELLING

        data_modelling_container = st.beta_container()
        with data_modelling_container:
            #st.write("")
            #st.write("")
            #st.write("")
            st.write("")
            st.write("")
            st.header("**Panel data modelling**")
            st.markdown("Go for creating predictive models of your panel data using panel data modelling!  Staty will take care of the modelling for you, so you can put your focus on results interpretation and communication! ")

            PDM_settings = st.beta_expander("Specify model", expanded = False)
            with PDM_settings:
                
                if time_na_warn == False and entity_na_warn == False:

                    # Initial status for running models
                    model_full_results = None
                    do_modval = "No"
                    model_val_results = None
                    model_full_results = None
                    panel_model_fit = None

                    if df.shape[1] > 2 and df.shape[0] > 0:

                        #--------------------------------------------------------------------------------------
                        # GENERAL SETTINGS
                    
                        st.markdown("**Variable selection**")

                        # Variable categories
                        df_summary_model = fc.data_summary(df)
                        var_cat = df_summary_model["Variable types"].loc["category"]

                        # Response variable
                        response_var_options = df.columns
                        response_var_options = response_var_options[response_var_options.isin(df.drop(entity, axis = 1).columns)]
                        if time != "NA":
                            response_var_options = response_var_options[response_var_options.isin(df.drop(time, axis = 1).columns)]
                        response_var = st.selectbox("Select response variable", response_var_options, key = session_state.id)

                        # Check if response variable is numeric and has no NAs
                        response_var_message_num = False
                        response_var_message_na = False
                        response_var_message_cat = False

                        if var_cat.loc[response_var] == "string/binary" or var_cat.loc[response_var] == "bool/binary":
                            response_var_message_num = "ERROR: Please select a numeric response variable!"
                        elif var_cat.loc[response_var] == "string/categorical" or var_cat.loc[response_var] == "other" or var_cat.loc[response_var] == "string/single":
                            response_var_message_num = "ERROR: Please select a numeric response variable!"
                        elif np.where(df[response_var].isnull())[0].size > 0:
                            response_var_message_na = "ERROR: Please select a response variable without NAs or delete/replace rows with NAs in data processing preferences!"
                        elif var_cat.loc[response_var] == "categorical":
                            response_var_message_cat = "WARNING: Categorical variable is treated as continuous variable!"

                        if response_var_message_num != False:
                            st.error(response_var_message_num)
                        if response_var_message_na != False:
                            st.error(response_var_message_na)
                        if response_var_message_cat != False:
                            st.warning(response_var_message_cat)

                        # Continue if everything is clean for response variable
                        if response_var_message_num == False and response_var_message_na == False:
                            # Select explanatory variables
                            expl_var_options = response_var_options[response_var_options.isin(df.drop(response_var, axis = 1).columns)]
                            expl_var = st.multiselect("Select explanatory variables", expl_var_options, key = session_state.id)

                            # Check if explanatory variables are numeric and have no NAs
                            expl_var_message_num = False
                            expl_var_message_na = False
                            if any(a for a in df[expl_var].dtypes if a != "float64" and a != "float32" and a != "int64" and a != "int64"): 
                                expl_var_not_num = df[expl_var].select_dtypes(exclude=["int64", "int32", "float64", "float32"]).columns
                                expl_var_message_num = "ERROR: Please exclude non-numeric variables: " + ', '.join(map(str,list(expl_var_not_num)))
                            elif np.where(df[expl_var].isnull())[0].size > 0:
                                expl_var_with_na = df[expl_var].columns[df[expl_var].isna().any()].tolist()
                                expl_var_message_na = "ERROR: Please select variables without NAs or delete/replace rows with NAs in data processing preferences: " + ', '.join(map(str,list(expl_var_with_na)))

                            if expl_var_message_num != False:
                                st.error(expl_var_message_num)
                            elif expl_var_message_na != False:
                                st.error(expl_var_message_na)
                            # Continue if everything is clean for explanatory variables and at least one was selected
                            elif expl_var_message_num == False and expl_var_message_na == False and len(expl_var) > 0:
                            
                                #--------------------------------------------------------------------------------------
                                # ALGORITHMS

                                st.markdown("**Specify modelling algorithm**")

                                # Algorithms selection
                                algorithms = ["Entity Fixed Effects", "Time Fixed Effects", "Two-ways Fixed Effects", "Random Effects", "Pooled"]
                                PDM_alg = st.selectbox("Select modelling technique", algorithms)
                                
                                # Covariance type
                                PDM_cov_type = st.selectbox("Select covariance type", ["homoskedastic", "heteroskedastic", "clustered"])
                                PDM_cov_type2 = None 
                                if PDM_cov_type == "clustered":
                                    PDM_cov_type2 = st.selectbox("Select cluster type", ["entity", "time", "both"])

                                #--------------------------------------------------------------------------------------
                                # VALIDATION SETTINGS

                                st.markdown("**Validation settings**")

                                do_modval= st.selectbox("Use model validation", ["No", "Yes"])

                                if do_modval == "Yes":
                                    # Select training/ test ratio 
                                    train_frac = st.slider("Select training data size", 0.5, 0.95, 0.8)

                                    # Select number for validation runs
                                    val_runs = st.slider("Select number for validation runs", 5, 100, 10)

                                #--------------------------------------------------------------------------------------
                                # SETTINGS SUMMARY

                                st.write("")
                                if st.checkbox('Show a summary of modelling settings', value = False): 
                                    
                                    #--------------------------------------------------------------------------------------
                                    # ALOGRITHMS
                                    
                                    st.write("Algorithms summary:")
                                    st.write("- ",PDM_alg)
                                    st.write("- Covariance type: ", PDM_cov_type)
                                    if PDM_cov_type2 is not None:
                                        st.write("- Cluster type: ", PDM_cov_type2)
                                    st.write("")

                                    #--------------------------------------------------------------------------------------
                                    # SETTINGS

                                    # General settings summary
                                    st.write("General settings summary:")
                                    # Modelling formula
                                    if expl_var != False:
                                        st.write("- Modelling formula:", response_var, "~",  ' + '.join(expl_var))
                                        st.write("- Entity:", entity)
                                        st.write("- Time:", time)
                                    if do_modval == "Yes":
                                        # Train/ test ratio
                                        if train_frac != False:
                                            st.write("- Train/ test ratio:", str(round(train_frac*100)), "% / ", str(round(100-train_frac*100)), "%")
                                        # Validation runs
                                        if val_runs != False:
                                            st.write("- Validation runs:", str(val_runs))
                                    st.write("")
                                    st.write("")
                                
                                #--------------------------------------------------------------------------------------
                                # RUN MODELS

                                # Models are run on button click
                                st.write("")
                                run_models = st.button("Run model")
                                st.write("")

                                # Run everything on button click
                                if run_models:

                                    # Define clustered cov matrix "entity", "time", "both"
                                    cluster_entity = True
                                    cluster_time = False
                                    if PDM_cov_type == "clustered":
                                        if PDM_cov_type2 == "entity":
                                            cluster_entity = True
                                            cluster_time = False
                                        if PDM_cov_type2 == "time":
                                            cluster_entity = False
                                            cluster_time = True
                                        if PDM_cov_type2 == "both":
                                            cluster_entity = True
                                            cluster_time = True

                                    # Prepare data
                                    data = df.set_index([entity, time])
                                    Y_data = data[response_var]
                                    X_data1 = data[expl_var] # for efe, tfe, twfe
                                    X_data2 = sm.add_constant(data[expl_var]) # for re, pool

                                    # Model validation
                                    if do_modval == "Yes":
                                        # Progress bar
                                        st.info("Validation progress")
                                        my_bar = st.progress(0.0)
                                        progress1 = 0

                                        # Model validation
                                        # R²
                                        model_eval_r2 = pd.DataFrame(index = range(val_runs), columns = [response_var])
                                        # MSE
                                        model_eval_mse = pd.DataFrame(index = range(val_runs), columns = ["Value"])
                                        # RMSE
                                        model_eval_rmse = pd.DataFrame(index = range(val_runs), columns = ["Value"])
                                        # MAE
                                        model_eval_mae = pd.DataFrame(index = range(val_runs), columns = ["Value"])
                                        # MaxERR
                                        model_eval_maxerr = pd.DataFrame(index = range(val_runs), columns = ["Value"])
                                        # EVRS
                                        model_eval_evrs = pd.DataFrame(index = range(val_runs), columns = ["Value"])
                                        # SSR
                                        model_eval_ssr = pd.DataFrame(index = range(val_runs), columns = ["Value"])

                                        # Model validation summary
                                        model_eval_mean = pd.DataFrame(index = ["% VE", "MSE", "RMSE", "MAE", "MaxErr", "EVRS", "SSR"], columns = ["Value"])
                                        model_eval_sd = pd.DataFrame(index = ["% VE", "MSE", "RMSE", "MAE", "MaxErr", "EVRS", "SSR"], columns = ["Value"])

                                        # Collect all residuals in test runs
                                        resdiuals_allruns = {}

                                        for val in range(val_runs):
                                            
                                            # Split data into train/ test data
                                            if PDM_alg != "Pooled" and PDM_alg != "Random Effects":
                                                X_data = X_data1.copy()
                                            if PDM_alg == "Pooled" or PDM_alg == "Random Effects":
                                                X_data = X_data2.copy()
                                            X_train, X_test, Y_train, Y_test = train_test_split(X_data, Y_data, train_size = train_frac, random_state = val)

                                            # Train selected panel model
                                            # efe
                                            panel_model_efe_val = PanelOLS(Y_train, X_train, entity_effects = True, time_effects = False)
                                            panel_model_fit_efe_val = panel_model_efe_val.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                            # tfe
                                            panel_model_tfe_val = PanelOLS(Y_train, X_train, entity_effects = False, time_effects = True)
                                            panel_model_fit_tfe_val = panel_model_tfe_val.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                            # twfe
                                            panel_model_twfe_val = PanelOLS(Y_train, X_train, entity_effects = True, time_effects = True)
                                            panel_model_fit_twfe_val = panel_model_twfe_val.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                            # re
                                            panel_model_re_val = RandomEffects(Y_train, X_train)
                                            panel_model_fit_re_val = panel_model_re_val.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True)
                                            # pool
                                            panel_model_pool_val = PooledOLS(Y_train, X_train)
                                            panel_model_fit_pool_val = panel_model_pool_val.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True)                   
                                            # save selected model
                                            if PDM_alg == "Entity Fixed Effects":
                                                panel_model_fit_val = panel_model_fit_efe_val
                                            if PDM_alg == "Time Fixed Effects":
                                                panel_model_fit_val = panel_model_fit_tfe_val
                                            if PDM_alg == "Two-ways Fixed Effects":
                                                panel_model_fit_val = panel_model_fit_twfe_val
                                            if PDM_alg == "Random Effects":
                                                panel_model_fit_val = panel_model_fit_re_val
                                            if PDM_alg == "Pooled":
                                                panel_model_fit_val = panel_model_fit_pool_val
                                            
                                            # Extract effects
                                            if PDM_alg != "Pooled":
                                                comb_effects = panel_model_fit_val.estimated_effects
                                            ent_effects = pd.DataFrame(index = X_train.reset_index()[entity].drop_duplicates(), columns = ["Value"])
                                            time_effects = pd.DataFrame(index = sorted(list(X_train.reset_index()[time].drop_duplicates().drop_duplicates())), columns = ["Value"])

                                            # Use LSDV for estimating effects
                                            if PDM_alg == "Entity Fixed Effects":
                                                X_train_mlr = pd.concat([X_train.reset_index(drop = True), pd.get_dummies(X_train.reset_index()[entity])], axis = 1)
                                                Y_train_mlr = Y_train.reset_index(drop = True)
                                                model_mlr_val = sm.OLS(Y_train_mlr, X_train_mlr)
                                                model_mlr_fit_val = model_mlr_val.fit()
                                                for e in ent_effects.index:
                                                    ent_effects.loc[e]["Value"] = model_mlr_fit_val.params[e]
                                                for t in time_effects.index:
                                                    time_effects.loc[t]["Value"] = 0
                                            if PDM_alg == "Time Fixed Effects":
                                                X_train_mlr = pd.concat([X_train.reset_index(drop = True), pd.get_dummies(X_train.reset_index()[time])], axis = 1)
                                                Y_train_mlr = Y_train.reset_index(drop = True)
                                                model_mlr_val = sm.OLS(Y_train_mlr, X_train_mlr)
                                                model_mlr_fit_val = model_mlr_val.fit()
                                                for e in ent_effects.index:
                                                    ent_effects.loc[e]["Value"] = 0
                                                for t in time_effects.index:
                                                    time_effects.loc[t]["Value"] = model_mlr_fit_val.params[t]
                                            if PDM_alg == "Two-ways Fixed Effects":
                                                X_train_mlr = pd.concat([X_train.reset_index(drop = True), pd.get_dummies(X_train.reset_index()[entity]), pd.get_dummies(X_train.reset_index()[time])], axis = 1)
                                                Y_train_mlr = Y_train.reset_index(drop = True)
                                                model_mlr_val = sm.OLS(Y_train_mlr, X_train_mlr)
                                                model_mlr_fit_val = model_mlr_val.fit()
                                                for e in ent_effects.index:
                                                    ent_effects.loc[e]["Value"] = model_mlr_fit_val.params[e]
                                                for t in time_effects.index:
                                                    time_effects.loc[t]["Value"] = model_mlr_fit_val.params[t]
                                            if PDM_alg == "Random Effects":
                                                for e in ent_effects.index:
                                                    ent_effects.loc[e]["Value"] = comb_effects.loc[e,].reset_index(drop = True).iloc[0][0]
                                            
                                            # Prediction for Y_test (without including effects)
                                            Y_test_pred = panel_model_fit_val.predict(X_test)

                                            # Add effects for predictions
                                            for p in range(Y_test_pred.size):
                                                
                                                entity_ind = Y_test_pred.index[p][0]
                                                time_ind = Y_test_pred.index[p][1]
                                                
                                                # if effects are available, add effect
                                                if PDM_alg == "Entity Fixed Effects":
                                                    if any(a for a in ent_effects.index if a == entity_ind):
                                                        effect = ent_effects.loc[entity_ind][0]
                                                        Y_test_pred["predictions"].loc[entity_ind, time_ind] = Y_test_pred["predictions"].loc[entity_ind, time_ind] + effect
                                                if PDM_alg == "Time Fixed Effects":
                                                    if any(a for a in time_effects.index if a == time_ind):
                                                        effect = time_effects.loc[time_ind][0]
                                                        Y_test_pred["predictions"].loc[entity_ind, time_ind] = Y_test_pred["predictions"].loc[entity_ind, time_ind] + effect
                                                if PDM_alg == "Two-ways Fixed Effects":
                                                    if any(a for a in time_effects.index if a == time_ind):
                                                        effect_time = time_effects.loc[time_ind][0]
                                                    else: effect_time = 0
                                                    if any(a for a in ent_effects.index if a == entity_ind):
                                                        effect_entity = ent_effects.loc[entity_ind][0]
                                                    else: effect_entity = 0    
                                                    Y_test_pred["predictions"].loc[entity_ind, time_ind] = Y_test_pred["predictions"].loc[entity_ind, time_ind] + effect_entity + effect_time
                                                if PDM_alg == "Random Effects":
                                                    if any(a for a in ent_effects.index if a == entity_ind):
                                                        effect = ent_effects.loc[entity_ind][0]
                                                        Y_test_pred["predictions"].loc[entity_ind, time_ind] = Y_test_pred["predictions"].loc[entity_ind, time_ind] + effect

                                            # Adjust format
                                            Y_test_pred = Y_test_pred.reset_index()["predictions"]
                                            Y_test = Y_test.reset_index()[response_var]

                                            # Save R² for test data
                                            model_eval_r2.iloc[val][response_var] = r2_score(Y_test, Y_test_pred)

                                            # Save MSE for test data
                                            model_eval_mse.iloc[val]["Value"] = mean_squared_error(Y_test, Y_test_pred, squared = True)

                                            # Save RMSE for test data
                                            model_eval_rmse.iloc[val]["Value"] = mean_squared_error(Y_test, Y_test_pred, squared = False)

                                            # Save MAE for test data
                                            model_eval_mae.iloc[val]["Value"] = mean_absolute_error(Y_test, Y_test_pred)

                                            # Save MaxERR for test data
                                            model_eval_maxerr.iloc[val]["Value"] = max_error(Y_test, Y_test_pred)

                                            # Save explained variance regression score for test data
                                            model_eval_evrs.iloc[val]["Value"] = explained_variance_score(Y_test, Y_test_pred)

                                            # Save sum of squared residuals for test data
                                            model_eval_ssr.iloc[val]["Value"] = ((Y_test-Y_test_pred)**2).sum()

                                            # Save residual values for test data 
                                            res = Y_test-Y_test_pred
                                            resdiuals_allruns[val] = res

                                            progress1 += 1
                                            my_bar.progress(progress1/(val_runs))
                                        
                                        # Calculate mean performance statistics
                                        # Mean
                                        model_eval_mean.loc["% VE"]["Value"] = model_eval_r2[response_var].mean()
                                        model_eval_mean.loc["MSE"]["Value"] = model_eval_mse["Value"].mean()
                                        model_eval_mean.loc["RMSE"]["Value"] = model_eval_rmse["Value"].mean()
                                        model_eval_mean.loc["MAE"]["Value"] = model_eval_mae["Value"].mean()
                                        model_eval_mean.loc["MaxErr"]["Value"] = model_eval_maxerr["Value"].mean()
                                        model_eval_mean.loc["EVRS"]["Value"] = model_eval_evrs["Value"].mean()
                                        model_eval_mean.loc["SSR"]["Value"] = model_eval_ssr["Value"].mean()
                                        # Sd
                                        model_eval_sd.loc["% VE"]["Value"] = model_eval_r2[response_var].std()
                                        model_eval_sd.loc["MSE"]["Value"] = model_eval_mse["Value"].std()
                                        model_eval_sd.loc["RMSE"]["Value"] = model_eval_rmse["Value"].std()
                                        model_eval_sd.loc["MAE"]["Value"] = model_eval_mae["Value"].std()
                                        model_eval_sd.loc["MaxErr"]["Value"] = model_eval_maxerr["Value"].std()
                                        model_eval_sd.loc["EVRS"]["Value"] = model_eval_evrs["Value"].std()
                                        model_eval_sd.loc["SSR"]["Value"] = model_eval_ssr["Value"].std()
                                        # Residuals 
                                        residuals_collection = pd.DataFrame()
                                        for x in resdiuals_allruns: 
                                            residuals_collection = residuals_collection.append(pd.DataFrame(resdiuals_allruns[x]), ignore_index = True)
                                        residuals_collection.columns = [response_var]
                                    
                                        # Collect validation results
                                        model_val_results = {}
                                        model_val_results["mean"] = model_eval_mean
                                        model_val_results["sd"] = model_eval_sd
                                        model_val_results["residuals"] = residuals_collection
                                        model_val_results["variance explained"] = model_eval_r2

                                    # Full model
                                    # Progress bar
                                    st.info("Full model progress")
                                    my_bar_fm = st.progress(0.0)
                                    progress2 = 0
                                    # efe
                                    panel_model_efe = PanelOLS(Y_data, X_data1, entity_effects = True, time_effects = False)
                                    panel_model_fit_efe = panel_model_efe.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                    # tfe
                                    panel_model_tfe = PanelOLS(Y_data, X_data1, entity_effects = False, time_effects = True)
                                    panel_model_fit_tfe = panel_model_tfe.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                    # twfe
                                    panel_model_twfe = PanelOLS(Y_data, X_data1, entity_effects = True, time_effects = True)
                                    panel_model_fit_twfe = panel_model_twfe.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True) 
                                    # re
                                    panel_model_re = RandomEffects(Y_data, X_data2)
                                    panel_model_fit_re = panel_model_re.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True)
                                    # pool
                                    panel_model_pool = PooledOLS(Y_data, X_data2)
                                    panel_model_fit_pool = panel_model_pool.fit(cov_type = PDM_cov_type, cluster_entity = cluster_entity, cluster_time = cluster_time, debiased = True, auto_df = True)                   
                                    # save selected model
                                    if PDM_alg == "Entity Fixed Effects":
                                        panel_model_fit = panel_model_fit_efe
                                    if PDM_alg == "Time Fixed Effects":
                                        panel_model_fit = panel_model_fit_tfe
                                    if PDM_alg == "Two-ways Fixed Effects":
                                        panel_model_fit = panel_model_fit_twfe
                                    if PDM_alg == "Random Effects":
                                        panel_model_fit = panel_model_fit_re
                                    if PDM_alg == "Pooled":
                                        panel_model_fit = panel_model_fit_pool
                                        

                                    # Entity information
                                    ent_inf = pd.DataFrame(index = ["No. entities", "Avg observations", "Median observations", "Min observations", "Max observations"], columns = ["Value"])
                                    ent_inf.loc["No. entities"] = panel_model_fit.entity_info["total"]
                                    ent_inf.loc["Avg observations"] = panel_model_fit.entity_info["mean"]
                                    ent_inf.loc["Median observations"] = panel_model_fit.entity_info["median"]
                                    ent_inf.loc["Min observations"] = panel_model_fit.entity_info["min"]
                                    ent_inf.loc["Max observations"] = panel_model_fit.entity_info["max"]

                                    # Time information
                                    time_inf = pd.DataFrame(index = ["No. time periods", "Avg observations", "Median observations", "Min observations", "Max observations"], columns = ["Value"])
                                    time_inf.loc["No. time periods"] = panel_model_fit.time_info["total"]
                                    time_inf.loc["Avg observations"] = panel_model_fit.time_info["mean"]
                                    time_inf.loc["Median observations"] = panel_model_fit.time_info["median"]
                                    time_inf.loc["Min observations"] = panel_model_fit.time_info["min"]
                                    time_inf.loc["Max observations"] = panel_model_fit.time_info["max"]

                                    # Regression information
                                    reg_inf = pd.DataFrame(index = ["Dep. variable", "Estimator", "Method", "No. observations", "DF residuals", "DF model", "Covariance type"], columns = ["Value"])
                                    reg_inf.loc["Dep. variable"] = response_var
                                    reg_inf.loc["Estimator"] =  panel_model_fit.name
                                    if PDM_alg == "Entity Fixed Effects" or PDM_alg == "Time Fixed Effects" or "Two-ways Fixed":
                                        reg_inf.loc["Method"] = "Within"
                                    if PDM_alg == "Random Effects":
                                        reg_inf.loc["Method"] = "Quasi-demeaned"
                                    if PDM_alg == "Pooled":
                                        reg_inf.loc["Method"] = "Least squares"
                                    reg_inf.loc["No. observations"] = panel_model_fit.nobs
                                    reg_inf.loc["DF residuals"] = panel_model_fit.df_resid
                                    reg_inf.loc["DF model"] = panel_model_fit.df_model
                                    reg_inf.loc["Covariance type"] = panel_model_fit._cov_type

                                    # Regression statistics
                                    fitted = df[response_var]-panel_model_fit.resids.values
                                    obs = df[response_var]
                                    reg_stats = pd.DataFrame(index = ["R²", "R² (between)", "R² (within)", "R² (overall)", "Log-likelihood", "SST", "SST (overall)"], columns = ["Value"])
                                    reg_stats.loc["R²"] = panel_model_fit._r2
                                    reg_stats.loc["R² (between)"] = panel_model_fit._c2b**2
                                    reg_stats.loc["R² (within)"] = panel_model_fit._c2w**2
                                    reg_stats.loc["R² (overall)"] = panel_model_fit._c2o**2
                                    reg_stats.loc["Log-likelihood"] = panel_model_fit._loglik
                                    reg_stats.loc["SST"] = panel_model_fit.total_ss
                                    reg_stats.loc["SST (overall)"] = ((obs-obs.mean())**2).sum()

                                    # Overall performance metrics (with effects)
                                    reg_overall = pd.DataFrame(index = ["% VE", "MSE", "RMSE", "MAE", "MaxErr", "EVRS", "SSR"], columns = ["Value"])
                                    reg_overall.loc["% VE"] = r2_score(obs, fitted)
                                    reg_overall.loc["MSE"] = mean_squared_error(obs, fitted, squared = True)
                                    reg_overall.loc["RMSE"] = mean_squared_error(obs, fitted, squared = False)
                                    reg_overall.loc["MAE"] = mean_absolute_error(obs, fitted)
                                    reg_overall.loc["MaxErr"] = max_error(obs, fitted)
                                    reg_overall.loc["EVRS"] = explained_variance_score(obs, fitted)
                                    reg_overall.loc["SSR"] = ((obs-fitted)**2).sum()

                                    # ANOVA
                                    if PDM_alg == "Pooled":
                                        Y_data_mlr = df[response_var]
                                        X_data_mlr = sm.add_constant(df[expl_var])
                                        full_model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                                        full_model_fit = full_model_mlr.fit()
                                        reg_anova = pd.DataFrame(index = ["Regression", "Residual", "Total"], columns = ["DF", "SS", "MS", "F-statistic"])
                                        reg_anova.loc["Regression"]["DF"] = full_model_fit.df_model
                                        reg_anova.loc["Regression"]["SS"] = full_model_fit.ess
                                        reg_anova.loc["Regression"]["MS"] = full_model_fit.ess/full_model_fit.df_model
                                        reg_anova.loc["Regression"]["F-statistic"] = full_model_fit.fvalue
                                        reg_anova.loc["Residual"]["DF"] = full_model_fit.df_resid
                                        reg_anova.loc["Residual"]["SS"] = full_model_fit.ssr
                                        reg_anova.loc["Residual"]["MS"] = full_model_fit.ssr/full_model_fit.df_resid
                                        reg_anova.loc["Residual"]["F-statistic"] = ""
                                        reg_anova.loc["Total"]["DF"] = full_model_fit.df_resid + full_model_fit.df_model
                                        reg_anova.loc["Total"]["SS"] = full_model_fit.ssr + full_model_fit.ess
                                        reg_anova.loc["Total"]["MS"] = ""
                                        reg_anova.loc["Total"]["F-statistic"] = ""

                                    # Coefficients
                                    if PDM_alg == "Entity Fixed Effects" or PDM_alg == "Time Fixed Effects" or "Two-ways Fixed Effects":
                                        reg_coef = pd.DataFrame(index = expl_var, columns = ["coeff", "std err", "t-statistic", "p-value", "lower 95%", "upper 95%"])
                                        for c in expl_var:
                                            reg_coef.loc[c]["coeff"] = panel_model_fit.params[expl_var.index(c)]
                                            reg_coef.loc[c]["std err"] = panel_model_fit.std_errors.loc[c]
                                            reg_coef.loc[c]["t-statistic"] = panel_model_fit.tstats.loc[c]
                                            reg_coef.loc[c]["p-value"] = panel_model_fit.pvalues.loc[c]
                                            reg_coef.loc[c]["lower 95%"] = panel_model_fit.conf_int(level = 0.95).loc[c]["lower"]
                                            reg_coef.loc[c]["upper 95%"] = panel_model_fit.conf_int(level = 0.95).loc[c]["upper"]
                                    if PDM_alg == "Random Effects" or PDM_alg == "Pooled":
                                        reg_coef = pd.DataFrame(index = ["const"]+ expl_var, columns = ["coeff", "std err", "t-statistic", "p-value", "lower 95%", "upper 95%"])
                                        for c in ["const"] + expl_var:
                                            reg_coef.loc[c]["coeff"] = panel_model_fit.params[(["const"]+ expl_var).index(c)]
                                            reg_coef.loc[c]["std err"] = panel_model_fit.std_errors.loc[c]
                                            reg_coef.loc[c]["t-statistic"] = panel_model_fit.tstats.loc[c]
                                            reg_coef.loc[c]["p-value"] = panel_model_fit.pvalues.loc[c]
                                            reg_coef.loc[c]["lower 95%"] = panel_model_fit.conf_int(level = 0.95).loc[c]["lower"]
                                            reg_coef.loc[c]["upper 95%"] = panel_model_fit.conf_int(level = 0.95).loc[c]["upper"]
                                    
                                    # Effects
                                    reg_ent_effects = pd.DataFrame(index = df[entity].drop_duplicates(), columns = ["Value"])
                                    reg_time_effects = pd.DataFrame(index = sorted(list(df[time].drop_duplicates())), columns = ["Value"])
                                    reg_comb_effects = panel_model_fit.estimated_effects
                                    reg_comb_effects.columns = ["Value"]
                                    # Use LSDV for estimating effects
                                    Y_data_mlr = df[response_var]
                                    if PDM_alg == "Pooled" or PDM_alg == "Random Effects":
                                        X_data_mlr = sm.add_constant(df[expl_var])
                                    else: X_data_mlr = df[expl_var]

                                    if PDM_alg == "Entity Fixed Effects":
                                        X_data_mlr = pd.concat([X_data_mlr, pd.get_dummies(df[entity])], axis = 1)
                                        model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                                        model_mlr_fit = model_mlr.fit()
                                        for e in reg_ent_effects.index:
                                            reg_ent_effects.loc[e]["Value"] = model_mlr_fit.params[e]
                                        for t in reg_time_effects.index:
                                            reg_time_effects.loc[t]["Value"] = 0
                                    if PDM_alg == "Time Fixed Effects":
                                        X_data_mlr = pd.concat([X_data_mlr, pd.get_dummies(df[time])], axis = 1)
                                        model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                                        model_mlr_fit = model_mlr.fit()
                                        for e in reg_ent_effects.index:
                                            reg_ent_effects.loc[e]["Value"] = 0
                                        for t in reg_time_effects.index:
                                            reg_time_effects.loc[t]["Value"] = model_mlr_fit.params[t]
                                    if PDM_alg == "Two-ways Fixed Effects":
                                        X_data_mlr = pd.concat([X_data_mlr, pd.get_dummies(df[entity]), pd.get_dummies(df[time])], axis = 1)
                                        model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                                        model_mlr_fit = model_mlr.fit()
                                        for e in reg_ent_effects.index:
                                            reg_ent_effects.loc[e]["Value"] = model_mlr_fit.params[e]
                                        for t in reg_time_effects.index:
                                            reg_time_effects.loc[t]["Value"] = model_mlr_fit.params[t]
                                    if PDM_alg == "Random Effects":
                                        for e in reg_ent_effects.index:
                                            reg_ent_effects.loc[e]["Value"] = reg_comb_effects.loc[e,].reset_index(drop = True).iloc[0][0]
                                        for t in reg_time_effects.index:
                                            reg_time_effects.loc[t]["Value"] = 0
                                    
                                    # Variance decomposition
                                    if PDM_alg == "Random Effects":
                                        reg_var_decomp = pd.DataFrame(index = ["idiosyncratic", "individual"], columns = ["variance", "share"])
                                        reg_theta = pd.DataFrame(index = ["theta"], columns = df[entity].drop_duplicates())
                                        reg_var_decomp.loc["idiosyncratic"]["variance"] = panel_model_fit.variance_decomposition["Residual"]
                                        reg_var_decomp.loc["individual"]["variance"] = panel_model_fit.variance_decomposition["Effects"]
                                        reg_var_decomp.loc["idiosyncratic"]["share"] = panel_model_fit.variance_decomposition["Residual"]/(panel_model_fit.variance_decomposition["Residual"]+panel_model_fit.variance_decomposition["Effects"])
                                        reg_var_decomp.loc["individual"]["share"] = panel_model_fit.variance_decomposition["Effects"]/(panel_model_fit.variance_decomposition["Residual"]+panel_model_fit.variance_decomposition["Effects"])
                                        reg_theta.loc["theta"] = list(panel_model_fit.theta.values)
                                    
                                    # Statistical tests
                                    if PDM_alg == "Entity Fixed Effects":
                                        if PDM_cov_type == "homoskedastic":
                                            reg_test = pd.DataFrame(index = ["test statistic", "p-value", "distribution"], columns = ["F-test (non-robust)", "F-test (robust)", "F-test (poolability)", "Hausman-test"])
                                        else:
                                            reg_test = pd.DataFrame(index = ["test statistic", "p-value", "distribution"], columns = ["F-test (non-robust)", "F-test (robust)", "F-test (poolability)"])
                                    else:
                                        reg_test = pd.DataFrame(index = ["test statistic", "p-value", "distribution"], columns = ["F-test (non-robust)", "F-test (robust)", "F-test (poolability)"])
                                    if PDM_alg == "Pooled" or PDM_alg == "Random Effects":
                                        reg_test = pd.DataFrame(index = ["test statistic", "p-value", "distribution"], columns = ["F-test (non-robust)", "F-test (robust)"])
                                    reg_test.loc["test statistic"]["F-test (non-robust)"] = panel_model_fit.f_statistic.stat
                                    reg_test.loc["p-value"]["F-test (non-robust)"] = panel_model_fit.f_statistic.pval
                                    reg_test.loc["distribution"]["F-test (non-robust)"] = "F(" + str(panel_model_fit.f_statistic.df) + ", " + str(panel_model_fit.f_statistic.df_denom) + ")"
                                    reg_test.loc["test statistic"]["F-test (robust)"] = panel_model_fit.f_statistic_robust.stat 
                                    reg_test.loc["p-value"]["F-test (robust)"] = panel_model_fit.f_statistic_robust.pval
                                    reg_test.loc["distribution"]["F-test (robust)"] = "F(" + str(panel_model_fit.f_statistic_robust.df) + ", " + str(panel_model_fit.f_statistic_robust.df_denom) + ")"
                                    if PDM_alg != "Pooled" and PDM_alg != "Random Effects" :
                                        reg_test.loc["test statistic"]["F-test (poolability)"] = panel_model_fit.f_pooled.stat
                                        reg_test.loc["p-value"]["F-test (poolability)"] = panel_model_fit.f_pooled.pval
                                        reg_test.loc["distribution"]["F-test (poolability)"] = "F(" + str(panel_model_fit.f_pooled.df) + ", " + str(panel_model_fit.f_pooled.df_denom) + ")"
                                    if PDM_alg == "Entity Fixed Effects":
                                        if PDM_cov_type == "homoskedastic":
                                            reg_test.loc["test statistic"]["Hausman-test"] = fc.hausman_test(panel_model_fit, panel_model_fit_re)[0] 
                                            reg_test.loc["p-value"]["Hausman-test"] = fc.hausman_test(panel_model_fit, panel_model_fit_re)[2] 
                                            reg_test.loc["distribution"]["Hausman-test"] = "Chi²(" + str(fc.hausman_test(panel_model_fit, panel_model_fit_re)[1])  + ")"
                            
                                    # Heteroskedasticity tests
                                    reg_het_test = pd.DataFrame(index = ["test statistic", "p-value"], columns = ["Breusch-Pagan test", "White test (without int.)", "White test (with int.)"])
                                    if PDM_alg == "Pooled":
                                        # Create datasets
                                        Y_data_mlr = df[response_var]
                                        X_data_mlr = sm.add_constant(df[expl_var])
                                        # Create MLR models 
                                        full_model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                                        full_model_fit = full_model_mlr.fit()
                                        # Breusch-Pagan heteroscedasticity test
                                        bp_result = sm.stats.diagnostic.het_breuschpagan(full_model_fit.resid, full_model_fit.model.exog) 
                                        reg_het_test.loc["test statistic"]["Breusch-Pagan test"] = bp_result[0]
                                        reg_het_test.loc["p-value"]["Breusch-Pagan test"] = bp_result[1]
                                        # White heteroscedasticity test with interaction
                                        white_int_result = sm.stats.diagnostic.het_white(full_model_fit.resid, full_model_fit.model.exog)
                                        reg_het_test.loc["test statistic"]["White test (with int.)"] = white_int_result[0]
                                        reg_het_test.loc["p-value"]["White test (with int.)"] = white_int_result[1]
                                        # White heteroscedasticity test without interaction
                                        X_data_mlr_white = X_data_mlr
                                        for i in expl_var: 
                                            X_data_mlr_white[i+ "_squared"] = X_data_mlr_white[i]**2
                                        white = sm.OLS(full_model_fit.resid**2, X_data_mlr_white)
                                        del X_data_mlr_white
                                        white_fit = white.fit()
                                        white_statistic = white_fit.rsquared*data.shape[0]
                                        white_p_value = stats.chi2.sf(white_statistic,len(white_fit.model.exog_names)-1)
                                        reg_het_test.loc["test statistic"]["White test (without int.)"] = white_statistic
                                        reg_het_test.loc["p-value"]["White test (without int.)"] = white_p_value
                                    
                                    # Residuals distribution
                                    reg_resid = pd.DataFrame(index = ["min", "25%-Q", "median", "75%-Q", "max"], columns = ["Value"])
                                    reg_resid.loc["min"]["Value"] = panel_model_fit.resids.min()
                                    reg_resid.loc["25%-Q"]["Value"] = panel_model_fit.resids.quantile(q = 0.25)
                                    reg_resid.loc["median"]["Value"] = panel_model_fit.resids.quantile(q = 0.5)
                                    reg_resid.loc["75%-Q"]["Value"] = panel_model_fit.resids.quantile(q = 0.75)
                                    reg_resid.loc["max"]["Value"] = panel_model_fit.resids.max()

                                    # Save full model results
                                    model_full_results = {}
                                    model_full_results["Entity information"] = ent_inf
                                    model_full_results["Time information"] = time_inf
                                    model_full_results["Regression information"] = reg_inf
                                    model_full_results["Regression statistics"] = reg_stats
                                    model_full_results["Overall performance"] = reg_overall
                                    if PDM_alg == "Pooled":
                                        model_full_results["ANOVA"] = reg_anova
                                    model_full_results["Coefficients"] = reg_coef
                                    model_full_results["Entity effects"] = reg_ent_effects
                                    model_full_results["Time effects"] = reg_time_effects
                                    model_full_results["Combined effects"] = reg_comb_effects
                                    if PDM_alg == "Random Effects":
                                        model_full_results["Variance decomposition"] = reg_var_decomp
                                        model_full_results["Theta"] = reg_theta
                                    model_full_results["tests"] = reg_test
                                    model_full_results["hetTests"] = reg_het_test
                                    model_full_results["Residuals"] = reg_resid
                                    
                                    progress2 += 1
                                    my_bar_fm.progress(progress2/1)
                                    # Success message
                                    st.success('Model run successfully!')
                    else: st.error("ERROR: No data available for Modelling!")

    #++++++++++++++++++++++
    # PDM OUTPUT

    # Show only if model was run (no further widgets after run models or the full page reloads)
    if run_models:
        st.write("")
        st.write("")
        st.header("**Model outputs**")

        #--------------------------------------------------------------------------------------
        # FULL MODEL OUTPUT

        full_output = st.beta_expander("Full model output", expanded = False)
        with full_output:

            if model_full_results is not None:

                st.markdown("**Correlation Matrix & 2D-Histogram**")
                # Define variable selector
                var_sel_cor = alt.selection_single(fields=['variable', 'variable2'], clear=False, 
                                    init={'variable': response_var, 'variable2': response_var})
                # Calculate correlation data
                corr_data = df[[response_var] + expl_var].corr().stack().reset_index().rename(columns={0: "correlation", 'level_0': "variable", 'level_1': "variable2"})
                corr_data["correlation_label"] = corr_data["correlation"].map('{:.2f}'.format)
                # Basic plot
                base = alt.Chart(corr_data).encode(
                    x = alt.X('variable2:O', sort = None, axis = alt.Axis(title = None, labelFontSize = 12)),
                    y = alt.Y('variable:O',  sort = None, axis = alt.Axis(title = None, labelFontSize = 12))
                )
                # Correlation values to insert
                text = base.mark_text().encode(
                    text='correlation_label',
                    color = alt.condition(
                        alt.datum.correlation > 0.5, 
                        alt.value('white'),
                        alt.value('black')
                    )
                )
                # Correlation plot
                corr_plot = base.mark_rect().encode(
                    color = alt.condition(var_sel_cor, alt.value('#86c29c'), 'correlation:Q', legend = alt.Legend(title = "Bravais-Pearson correlation coefficient", orient = "top", gradientLength = 350), scale = alt.Scale(scheme='redblue', reverse = True, domain = [-1,1]))
                ).add_selection(var_sel_cor)
                # Calculate values for 2d histogram
                value_columns = df[[response_var] + expl_var]
                df_2dbinned = pd.concat([fc.compute_2d_histogram(var1, var2, df) for var1 in value_columns for var2 in value_columns])
                # 2d binned histogram plot
                scat_plot = alt.Chart(df_2dbinned).transform_filter(
                    var_sel_cor
                ).mark_rect().encode(
                    alt.X('value2:N', sort = alt.EncodingSortField(field='raw_left_value2'), axis = alt.Axis(title = "Horizontal variable", labelFontSize = 12)), 
                    alt.Y('value:N', axis = alt.Axis(title = "Vertical variable", labelFontSize = 12), sort = alt.EncodingSortField(field='raw_left_value', order = 'descending')),
                    alt.Color('count:Q', scale = alt.Scale(scheme='reds'),  legend = alt.Legend(title = "Count", orient = "top", gradientLength = 350))
                )
                # Combine all plots
                correlation_plot = alt.vconcat((corr_plot + text).properties(width = 400, height = 400), scat_plot.properties(width = 400, height = 400)).resolve_scale(color = 'independent')
                correlation_plot = correlation_plot.properties(padding = {"left": 50, "top": 5, "right": 5, "bottom": 50})
                st.altair_chart(correlation_plot, use_container_width = True)
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_cor")))
                st.write("")

                #-------------------------------------------------------------

                # Regression output
                st.markdown("**Regression output**")

                full_out_col1, full_out_col2 = st.beta_columns(2)
                with full_out_col1:
                    # Entity information
                    st.write("Entity information:")
                    st.write(model_full_results["Entity information"])
                with full_out_col2:
                    # Time information
                    st.write("Time period information:")
                    st.write(model_full_results["Time information"])
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_pd_information")))
                st.write("")

                full_out_col3, full_out_col4 = st.beta_columns(2)
                with full_out_col3:
                    # Regression information
                    st.write("Regression information:")
                    st.write(model_full_results["Regression information"])
                with full_out_col4:
                    # Regression statistics
                    st.write("Regression statistics:")
                    st.write(model_full_results["Regression statistics"])
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_pd_regression")))
                st.write("")

                # Overall performance (with effects)
                full_out_col_op1, full_out_col_op2 = st.beta_columns(2)
                with full_out_col_op1:
                    if PDM_alg != "Pooled":
                        st.write("Overall performance (with effects):")
                    if PDM_alg == "Pooled":
                        st.write("Overall performance :")
                    st.write(model_full_results["Overall performance"])
                # Residuals
                with full_out_col_op2:
                    st.write("Residuals:")
                    st.write(model_full_results["Residuals"])     
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_pd_overallPerf")))
                st.write("")

                # Coefficients
                st.write("Coefficients:")
                st.write(model_full_results["Coefficients"])
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_pd_coef")))
                st.write("") 

                # Effects
                if PDM_alg != "Pooled":
                    full_out_col5, full_out_col6, full_out_col7 = st.beta_columns(3)
                    with full_out_col5:
                        st.write("Entity effects:")
                        st.write(model_full_results["Entity effects"])
                    with full_out_col6:
                        st.write("Time effects:")
                        st.write(model_full_results["Time effects"])
                    with full_out_col7:
                        st.write("Combined effects:")
                        st.write(model_full_results["Combined effects"])  
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_pd_effects")))
                    st.write("")  

                # ANOVA
                if PDM_alg == "Pooled":
                    st.write("ANOVA:")
                    st.write(model_full_results["ANOVA"])
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_pd_anova")))
                    st.write("")  

                # Statistical tests
                if PDM_alg == "Random Effects":
                    full_out_col_re1, full_out_col_re2 = st.beta_columns(2)
                    with full_out_col_re1:
                        st.write("Variance decomposition:")
                        st.write(model_full_results["Variance decomposition"])
                        st.write(model_full_results["Theta"])
                    with full_out_col_re2:
                        st.write("F-tests:")
                        st.write(model_full_results["tests"]) 
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_pd_testRE")))
                    st.write("")    
                if PDM_alg == "Entity Fixed Effects":
                    if PDM_cov_type == "homoskedastic":
                        st.write("F-tests and Hausman-test:")
                    else: st.write("F-tests:")
                    st.write(model_full_results["tests"])
                    if PDM_cov_type == "homoskedastic":
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_pd_testEFE_homosk")))
                    else:
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_pd_testEFE")))
                    st.write("")  
                if PDM_alg != "Entity Fixed Effects" and PDM_alg != "Random Effects":
                    st.write("F-tests:")
                    st.write(model_full_results["tests"])
                    if PDM_alg == "Pooled":
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_pd_test_pooled")))
                    else: 
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_pd_test"))) 
                    st.write("") 

                # Heteroskedasticity tests
                if PDM_alg == "Pooled":
                    st.write("Heteroskedasticity tests:")
                    st.write(model_full_results["hetTests"])
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_md_MLR_hetTest"))) 
                    st.write("")          

                # # Residuals
                # st.write("Residuals:")
                # full_out_col8, full_out_col9 = st.beta_columns(2)
                # with full_out_col8:
                #     st.write(model_full_results["Residuals"])     
                #     st.write("")
                # with full_out_col9:
                #     res = panel_model_fit.resids.values.copy()
                #     residual_results = pd.DataFrame(res, columns = ["AbsResiduals"])
                #     residual_results["AbsResiduals"] = residual_results["AbsResiduals"].abs()
                #     residual_results["Index"] = df.index
                #     #residuals_bplot = pd.melt(residual_results, ignore_index = False, value_name = "Residuals")
                #     residuals_chart = alt.Chart(residual_results, height = 200).mark_bar(size = 2).encode(
                #         x = alt.X("Index", title = "index", axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                #         y = alt.Y("AbsResiduals", title = "abs(residuals)", axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                #         tooltip = ["AbsResiduals", "Index"]
                #     ).configure_axis(
                #         labelFontSize = 12,
                #         titleFontSize = 12
                #     )
                #     st.altair_chart(residuals_chart, use_container_width = True)
                
                # Graphical output
                full_out_col10, full_out_col11 = st.beta_columns(2)
                fitted_withEff = df[response_var]-panel_model_fit.resids.values
                with full_out_col10:
                    st.write("Observed vs Fitted:")
                    observed_fitted_data = pd.DataFrame()
                    observed_fitted_data["Observed"] = df[response_var]
                    observed_fitted_data["Fitted"] = list(fitted_withEff)
                    observed_fitted_data["Index"] = df.index
                    observed_fitted = alt.Chart(observed_fitted_data, height = 200).mark_circle(size=20).encode(
                        x = alt.X("Fitted", title = "fitted", scale = alt.Scale(domain = [min(observed_fitted_data["Fitted"]), max(observed_fitted_data["Fitted"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                        y = alt.Y("Observed", title = "observed", scale = alt.Scale(zero = False),  axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                        tooltip = ["Observed", "Fitted", "Index"]
                    )
                    observed_fitted_plot = observed_fitted + observed_fitted.transform_regression("Fitted", "Observed").mark_line(size = 2, color = "darkred")
                    st.altair_chart(observed_fitted_plot, use_container_width = True)
                with full_out_col11:
                    st.write("Residuals vs Fitted:")
                    residuals_fitted_data = pd.DataFrame()
                    residuals_fitted_data["Residuals"] = panel_model_fit.resids.values
                    residuals_fitted_data["Fitted"] = list(fitted_withEff)
                    residuals_fitted_data["Index"] = df.index
                    residuals_fitted = alt.Chart(residuals_fitted_data, height = 200).mark_circle(size=20).encode(
                        x = alt.X("Fitted", title = "fitted", scale = alt.Scale(domain = [min(residuals_fitted_data["Fitted"]), max(residuals_fitted_data["Fitted"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                        y = alt.Y("Residuals", title = "residuals", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                        tooltip = ["Residuals", "Fitted", "Index"]
                    )
                    residuals_fitted_plot = residuals_fitted + residuals_fitted.transform_loess("Fitted", "Residuals", bandwidth = 0.5).mark_line(size = 2, color = "darkred")
                    st.altair_chart(residuals_fitted_plot, use_container_width = True)
                if sett_hints:
                    st.info(str(fc.learning_hints("mod_md_MLR_obsResVsFit"))) 
                st.write("")
                if PDM_alg == "Pooled":
                    full_out_col12, full_out_col13 = st.beta_columns(2)
                    with full_out_col12:
                        st.write("Normal QQ-plot:")
                        residuals = panel_model_fit.resids.values
                        qq_plot_data = pd.DataFrame()
                        qq_plot_data["StandResiduals"] = (residuals - residuals.mean())/residuals.std()
                        qq_plot_data["Index"] = df.index
                        qq_plot_data = qq_plot_data.sort_values(by = ["StandResiduals"])
                        qq_plot_data["Theoretical quantiles"] = stats.probplot(residuals, dist="norm")[0][0]
                        qq_plot = alt.Chart(qq_plot_data, height = 200).mark_circle(size=20).encode(
                            x = alt.X("Theoretical quantiles", title = "theoretical quantiles", scale = alt.Scale(domain = [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            y = alt.Y("StandResiduals", title = "stand. residuals", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            tooltip = ["StandResiduals", "Theoretical quantiles", "Index"]
                        )
                        line = alt.Chart(
                            pd.DataFrame({"Theoretical quantiles": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])], "StandResiduals": [min(qq_plot_data["Theoretical quantiles"]), max(qq_plot_data["Theoretical quantiles"])]})).mark_line(size = 2, color = "darkred").encode(
                                    alt.X("Theoretical quantiles"),
                                    alt.Y("StandResiduals"),
                        )
                        st.altair_chart(qq_plot + line, use_container_width = True)
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_md_MLR_qqplot"))) 
                        st.write("")
                    with full_out_col13:
                        st.write("Scale-Location:")
                        scale_location_data = pd.DataFrame()
                        residuals = panel_model_fit.resids.values
                        scale_location_data["SqrtStandResiduals"] = np.sqrt(abs((residuals - residuals.mean())/residuals.std()))
                        scale_location_data["Fitted"] = panel_model_fit._fitted.values
                        scale_location_data["Index"] = df.index
                        scale_location = alt.Chart(scale_location_data, height = 200).mark_circle(size=20).encode(
                            x = alt.X("Fitted", title = "fitted", scale = alt.Scale(domain = [min(scale_location_data["Fitted"]), max(scale_location_data["Fitted"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            y = alt.Y("SqrtStandResiduals", title = "sqrt(|stand. residuals|)", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            tooltip = ["SqrtStandResiduals", "Fitted", "Index"]
                        )
                        scale_location_plot = scale_location + scale_location.transform_loess("Fitted", "SqrtStandResiduals", bandwidth = 0.5).mark_line(size = 2, color = "darkred")
                        st.altair_chart(scale_location_plot, use_container_width = True)
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_md_MLR_scaleLoc"))) 
                        st.write("")

                    full_out_col14, full_out_col15 = st.beta_columns(2)
                    Y_data_mlr = df[response_var]
                    X_data_mlr = sm.add_constant(df[expl_var])
                    full_model_mlr = sm.OLS(Y_data_mlr, X_data_mlr)
                    full_model_fit = full_model_mlr.fit()
                    with full_out_col14:
                        st.write("Residuals vs Leverage:")
                        residuals_leverage_data = pd.DataFrame()
                        residuals = panel_model_fit.resids.values
                        residuals_leverage_data["StandResiduals"] = (residuals - residuals.mean())/residuals.std()
                        residuals_leverage_data["Leverage"] = full_model_fit.get_influence().hat_matrix_diag
                        residuals_leverage_data["Index"] = df.index
                        residuals_leverage = alt.Chart(residuals_leverage_data, height = 200).mark_circle(size=20).encode(
                            x = alt.X("Leverage", title = "leverage", scale = alt.Scale(domain = [min(residuals_leverage_data["Leverage"]), max(residuals_leverage_data["Leverage"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            y = alt.Y("StandResiduals", title = "stand. residuals", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            tooltip = ["StandResiduals","Leverage", "Index"]
                        )
                        residuals_leverage_plot = residuals_leverage + residuals_leverage.transform_loess("Leverage", "StandResiduals", bandwidth = 0.5).mark_line(size = 2, color = "darkred")
                        st.altair_chart(residuals_leverage_plot, use_container_width = True)
                    with full_out_col15:
                        st.write("Cook's distance:")
                        cooksD_data = pd.DataFrame()
                        cooksD_data["CooksD"] = full_model_fit.get_influence().cooks_distance[0]
                        cooksD_data["Index"] = df.index
                        cooksD = alt.Chart(cooksD_data, height = 200).mark_bar(size = 2).encode(
                            x = alt.X("Index", title = "index", scale = alt.Scale(domain = [-1, max(cooksD_data["Index"])]), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            y = alt.Y("CooksD", title = "Cook's distance", scale = alt.Scale(zero = False), axis = alt.Axis(titleFontSize = 12, labelFontSize = 11)),
                            tooltip = ["CooksD", "Index"]
                        )
                        st.altair_chart(cooksD, use_container_width = True)
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_md_MLR_resVsLev_cooksD")))
                    st.write("")

        #--------------------------------------------------------------------------------------
        # VALIDATION OUTPUT
        
        if do_modval == "Yes":
            if PDM_alg == "Pooled":
                validation_output_name = "Validation output"
            if PDM_alg != "Pooled":
                validation_output_name = "Validation output (with effects)"
            val_output = st.beta_expander(validation_output_name, expanded = False)
            with val_output:
                if model_val_results is not None:
                    val_col1, val_col2 = st.beta_columns(2)

                    with val_col1:
                        # Metrics
                        st.write("Means of metrics across validation runs:")
                        st.write(model_val_results["mean"])
                    with val_col2:
                        # Metrics
                        st.write("SDs of metrics across validation runs:")
                        st.write(model_val_results["sd"])
                    if sett_hints:
                        st.info(str(fc.learning_hints("mod_pd_val_metrics"))) 
                    st.write("")
                    
                    val_col3, val_col4 = st.beta_columns(2)
                    with val_col3:
                        # Residuals boxplot
                        if model_val_results["residuals"] is not None:
                            st.write("Boxplot of residuals across validation runs:")
                            residual_results = model_val_results["residuals"]
                            residuals_bplot = pd.melt(residual_results, ignore_index = False, var_name = "Variable", value_name = "Residuals")
                            residuals_boxchart = alt.Chart(residuals_bplot, height = 200).mark_boxplot(color = "#1f77b4", median = dict(color = "darkred")).encode(
                                x = alt.X("Residuals", title = "residuals", scale = alt.Scale(domain = [min(residuals_bplot["Residuals"]), max(residuals_bplot["Residuals"])])),
                                y = alt.Y("Variable", scale = alt.Scale(zero = False), title = None)
                            ).configure_axis(
                                labelFontSize = 12,
                                titleFontSize = 12
                            )
                            # Scatterplot residuals
                            # residuals_scatter = alt.Chart(residuals_bplot, height = 200).mark_circle(size=60).encode(
                            #     x = "Value",
                            #     y = alt.Y("Algorithm", title = None),
                            #     color = alt.Color("Algorithm", legend=None)
                            # )
                            residuals_plot = residuals_boxchart #+ residuals_scatter
                            st.altair_chart(residuals_plot, use_container_width=True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("mod_pd_val_resBoxplot")))
                            st.write("")
                    with val_col4:
                        # Variance explained boxplot
                        if model_val_results["variance explained"] is not None:
                            st.write("Boxplot of % VE across validation runs:")
                            ve_results = model_val_results["variance explained"]
                            ve_bplot = pd.melt(ve_results, ignore_index = False, var_name = "Variable", value_name = "% VE")
                            ve_boxchart = alt.Chart(ve_bplot, height = 200).mark_boxplot(color = "#1f77b4", median = dict(color = "darkred")).encode(
                                x = alt.X("% VE", scale = alt.Scale(domain = [min(ve_bplot["% VE"]), max(ve_bplot["% VE"])])),
                                y = alt.Y("Variable", title = None)
                            ).configure_axis(
                                labelFontSize = 12,
                                titleFontSize = 12
                            )
                            st.altair_chart(ve_boxchart, use_container_width = True)
                            if sett_hints:
                                st.info(str(fc.learning_hints("mod_pd_val_VEBoxplot")))
                            st.write("")

                    # Residuals
                    if model_val_results["residuals"] is not None:
                        model_val_res = pd.DataFrame(index = ["min", "25%-Q", "median", "75%-Q", "max"], columns = ["Value"])
                        model_val_res.loc["min"]["Value"] = model_val_results["residuals"][response_var].min()
                        model_val_res.loc["25%-Q"]["Value"] = model_val_results["residuals"][response_var].quantile(q = 0.25)
                        model_val_res.loc["median"]["Value"] = model_val_results["residuals"][response_var].quantile(q = 0.5)
                        model_val_res.loc["75%-Q"]["Value"] = model_val_results["residuals"][response_var].quantile(q = 0.75)
                        model_val_res.loc["max"]["Value"] = model_val_results["residuals"][response_var].max()
                        st.write("Residuals distribution across all validation runs:")
                        st.write(model_val_res)
                        if sett_hints:
                            st.info(str(fc.learning_hints("mod_pd_val_res")))
                        st.write("")

#--------------------------------------------------------------------------------------