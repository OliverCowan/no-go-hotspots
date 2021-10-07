## Libraries
library(sf)
library(tidyverse)
library(glue)


# Import cluster CSVs -----------------------------------------------------
cluster_files <- list.files("Output", pattern = ".csv$", full.names = TRUE)
cluster_files



# Function to extract species lists and summary measures ------------------
extract_spp_list <- function(x){

  df <- read_csv(x)

  param_def <- str_replace(x,'Output/Table_', '') %>%
    str_replace(., ".csv", "")

  df %>%
    group_by(CLUSTER_ID, SENSFEAT, THEME, RL_STATUS) %>%
    tally() %>%
    arrange(CLUSTER_ID, THEME, SENSFEAT) %>%
    write_csv(glue("Output/species_lists/species_list_{param_def}.csv"))

  df %>%
    group_by(CLUSTER_ID) %>%
    summarise(n_species = length(unique(SENSFEAT)),
              n_polygons = length(SENSFEAT)) %>%
    write_csv(glue("Output/species_lists/spp_polygon_count_{param_def}.csv"))

  df %>%
    group_by(CLUSTER_ID) %>%
    summarise(n_species = length(unique(SENSFEAT)),
              n_polygons = length(SENSFEAT)) %>%
    ggplot(aes(x = CLUSTER_ID, y = n_species))+
    geom_bar(stat = 'identity')
  ggsave(glue("Output/species_lists/spp_cluster_count_{param_def}.jpg"))

  df %>%
    group_by(CLUSTER_ID) %>%
    summarise(n_species = length(unique(SENSFEAT)),
              n_polygons = length(SENSFEAT)) %>%
    ggplot(aes(x = CLUSTER_ID, y = n_polygons))+
    geom_bar(stat = 'identity')
  ggsave(glue("Output/species_lists/polygon_cluster_count_{param_def}.jpg"))

  df %>%
    group_by(CLUSTER_ID,RL_STATUS) %>%
    tally() %>%
    arrange(CLUSTER_ID,RL_STATUS) %>%
    write_csv(glue("Output/species_lists/rlstatus_count_{param_def}.csv"))


}


# Iterate through CSV list ------------------------------------------------
walk(.x = cluster_files,
     .f = extract_spp_list)
