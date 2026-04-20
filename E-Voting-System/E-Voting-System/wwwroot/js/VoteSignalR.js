const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/vote")
    .build();


connection.on("UpdateVoteCount", (section) => {
    const countSpan = document.getElementById('count' + section);
    if (countSpan) {
        let currentCount = parseInt(countSpan.textContent) || 0;
        currentCount += 1;
        countSpan.textContent = currentCount;
        countSpan.style.animation = 'none';
        void countSpan.offsetWidth;
        countSpan.style.animation = 'pulse 0.5s ease';
    }
});


connection.start()
    .then(() => console.log("SignalR Connected for Voting"))
    .catch(err => console.error("SignalR Connection Error: ", err));