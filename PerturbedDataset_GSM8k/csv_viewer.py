import streamlit as st
import pandas as pd

def load_csv(uploaded_file):
    """
    Load CSV file and handle potential encoding issues
    """
    df = pd.read_csv(uploaded_file, sep='\t')
    return df


def main():
    st.set_page_config(layout="wide")
    st.title("CSV Text Viewer")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Load the CSV
        df = load_csv(uploaded_file)
        
        if df is not None:
            # Ensure necessary columns exist
            required_columns = ["id", "question", "solution", "perturbed_solution", "clean_solution"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.warning(f"Missing columns: {', '.join(missing_columns)}")
                return
            
            # Streamline column selection
            df = df[required_columns]
            
            # Navigation
            # st.sidebar.header("Navigation")
            total_samples = len(df)
            current_index = st.number_input(
                "Select Sample", 
                min_value=0, 
                max_value=total_samples-1, 
                value=0
            )
            
            # Display current sample with clear separation
            st.markdown("---")  # Full-width horizontal line separator
            
            # Main content area with columns
            col1, col2 = st.columns([1, 1])
                        
            with col1:
                st.markdown("### Sample Details")

                # ID
                st.markdown("#### ID")
                st.write(df.iloc[current_index]['id'])
                
                # Question section
                st.markdown("#### Question")
                st.write(df.iloc[current_index]['question'])
                
                st.markdown("---")
                
                # Solution section
                st.markdown("#### Solution")
                st.write(df.iloc[current_index]['solution'])

            with col2:
                st.markdown("### Sample Text")
                
                # Clean text
                st.markdown("#### Clean Text")
                st.write(df.iloc[current_index]['clean_solution'])
                
                st.markdown("---")
                
                # Malicious text
                st.markdown("#### Malicious Text")
                st.write(df.iloc[current_index]['perturbed_solution'])
                
                st.markdown("---")
                
                # # Explanation section
                # st.markdown("#### Explanation")
                # st.write(df.iloc[current_index]['explanation'])

            
            # Navigation buttons
            st.markdown("---")
            # col1, col2, col3 = st.columns(3)
            
            # with col1:
            #     if st.button("◀️ Previous Sample") and current_index > 0:
            #         st.session_state.current_index = current_index - 1
            #         # st.rerun()
            
            # with col2:
            #     st.write(f"Sample {current_index + 1} of {total_samples}")
            
            # with col3:
            #     if st.button("Next Sample ▶️") and current_index < total_samples - 1:
            #         st.session_state.current_index = current_index + 1
            #         # st.rerun()

            

if __name__ == "__main__":
    main()