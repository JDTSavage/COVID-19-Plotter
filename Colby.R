colby <- read.csv("ColbyCovid.csv")

plot(x = 1:(length(colby[3,]) - 1), y = colby[3,2:length(colby[3,])], type = "l", ylim = c(0, max(colby[3,2:length(colby[1,])])))
lines(x = 1:(length(colby[1,]) - 1), y = colby[1,2:length(colby[1,])])
lines(x = 1:(length(colby[2,]) - 1), y = colby[2,2:length(colby[2,])])

