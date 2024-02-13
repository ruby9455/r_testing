import streamlit as st
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
pandas2ri.activate()
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.lib import grdevices
from PIL import Image
from io import BytesIO

r_script = """
result <- function() {
library(devtools)
devtools::install_github("tgerke/ggconsort")
library(ggconsort)
library(dplyr)
library(ggplot2)
library(glue)

study_cohorts <- 
  trial_data %>%
  cohort_start("Assessed for eligibility") %>%
  # Define cohorts using named expressions --------------------
# Notice that you can use previously defined cohorts in subsequent steps
cohort_define(
  consented = .full %>% 
    filter(declined != 1),
  consented_chemonaive = consented %>% 
    filter(prior_chemo != 1),
  randomized = consented_chemonaive %>% 
    filter(bone_mets != 1),
  treatment_a = randomized %>% 
    filter(treatment == "Drug A"),
  treatment_b = randomized %>% 
    filter(treatment == "Drug B"),
  # anti_join is useful for counting exclusions -------------
  excluded = anti_join(.full, randomized, by = "id"),
  excluded_declined = anti_join(.full, consented, by = "id"),
  excluded_chemo = anti_join(consented, consented_chemonaive, by = "id"),
  excluded_mets = anti_join(consented_chemonaive, randomized, by = "id")
) %>%
  # Provide text labels for cohorts ---------------------------
cohort_label(
  consented = "Consented",
  consented_chemonaive = "Chemotherapy naive",
  randomized = "Randomized",
  treatment_a = "Allocated to arm A",
  treatment_b = "Allocated to arm B",
  excluded = "Excluded",
  excluded_declined = "Declined to participate",
  excluded_chemo = "Prior chemotherapy",
  excluded_mets = "Bone metastasis"
)

study_consort <- study_cohorts %>%
  consort_box_add(
    "full", 0, 50, cohort_count_adorn(study_cohorts, .full)
  ) %>%
  consort_box_add(
    "exclusions", 20, 40, glue::glue(
      '{cohort_count_adorn(study_cohorts, excluded)}<br>
      • {cohort_count_adorn(study_cohorts, excluded_declined)}<br>
      • {cohort_count_adorn(study_cohorts, excluded_chemo)}<br>
      • {cohort_count_adorn(study_cohorts, excluded_mets)}
      ')
  ) %>%
  consort_box_add(
    "randomized", 0, 30, cohort_count_adorn(study_cohorts, randomized)
  ) %>%
  consort_box_add(
    "arm_a", -30, 10, cohort_count_adorn(study_cohorts, treatment_a)
  ) %>%
  consort_box_add(
    "arm_b", 30, 10, cohort_count_adorn(study_cohorts, treatment_b)
  ) %>%
  consort_arrow_add(
    end = "exclusions", end_side = "left", start_x = 0, start_y = 40
  ) %>%
  consort_arrow_add(
    "full", "bottom", "randomized", "top"
  ) %>% 
  consort_arrow_add(
    start_x = 0, start_y = 30, end_x = 0, end_y = 20,
  ) %>%
  consort_line_add(
    start_x = -30, start_y = 20, end_x = 30, end_y = 20,
  ) %>% 
  consort_arrow_add(
    end = "arm_a", end_side = "top", start_x = -30, start_y = 20
  ) %>%
  consort_arrow_add(
    end = "arm_b", end_side = "top", start_x = 30, start_y = 20
  )

study_consort %>%
  ggplot() + 
  geom_consort() +
  theme_consort(margin_h = 8, margin_v = 1) +
  # you can include other ggplot geoms, as needed -------------
ggtext::geom_richtext(
  aes(x = 0, y = 10, label = "Allocation"),
  fill = "#9bc0fc"
)
}
"""

ro.r(r_script)

result = ro.r['result']()

with grdevices.render_to_bytesio(grdevices.png, width=1024, height=896, res=150) as img:
        # Call the result function to generate the plot
        ro.r['print'](result)
data = img.getvalue()
image = Image.open(BytesIO(data))
st.image(image, caption='CONSORT Diagram', use_column_width=True)