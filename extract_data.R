#!/usr/bin/env Rscript

library(argparse)

p <- ArgumentParser()
p$add_argument("DIR")
args <- p$parse_args()

library(tidyverse)
library(rvest)


if(as.integer(args$DIR) < 20200430){
  xpath_pdbid <- "/html/body/div[2]/div[1]/div/div[3]/table/tbody/tr[*]/td[1]/a"
  xpath_table <- "/html/body/div[2]/div[1]/div/div[3]/div[3]/table/tbody/tr[*]/td[2]/table"
}else{
  xpath_pdbid <- "/html/body/div[2]/div[1]/div/div[3]/table/tbody/tr[*]/td[1]/a"
  xpath_table <- "/html/body/div[2]/div[1]/div/div[3]/table/tbody/tr[*]/td[2]/table"
}


xpath_text <- function(path, xpath){
  read_html(path) %>% 
    html_nodes(xpath = xpath) %>% 
    html_text()
}

xpath_get_table <- function(path, xpath){
  read_html(path) %>% 
    html_nodes(xpath = xpath) %>% 
    html_table() %>%
    map(~set_names(.x$X2, c("title", .x$X1[-1]))[c("title", "実験手法", "分子名称:")]) %>%
    invoke(rbind, .) %>%
    as_tibble()
}


rep_dir <- file.path(args$DIR, "rep")
rep_htmls <- list.files(path = rep_dir, pattern = "*.html", full.names = T)

all_dir <- file.path(args$DIR, "all")
all_htmls <- list.files(path = all_dir, pattern = "*.html", full.names = T)

out <- paste0(file.path(args$DIR), ".csv")

rep_pdbid <- tibble(
    pdbid = map(rep_htmls, xpath_text, xpath = xpath_pdbid),
    data = map(rep_htmls, xpath_get_table, xpath = xpath_table)
    ) %>% 
  unnest(cols = c(pdbid, data)) %>% 
  mutate(代表構造 = TRUE) %>% 
  rename(method = 実験手法, molecule = `分子名称:`)

entries <- tibble(
  pdbid = map(all_htmls, xpath_text, xpath = xpath_pdbid),
  data = map(all_htmls, xpath_get_table, xpath = xpath_table)) %>% 
  unnest(cols = c(pdbid, data)) %>% 
  rename(method = 実験手法, molecule = `分子名称:`)


pdb_table <- entries %>% full_join(rep_pdbid) %>% mutate(代表構造 = replace_na(代表構造, FALSE)) %>% distinct()

write.csv(pdb_table, out)

