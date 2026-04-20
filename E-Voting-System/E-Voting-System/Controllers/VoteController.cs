using E_Voting_System.Hubs;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;

namespace E_Voting_System.Controllers
{
    public class VoteController : Controller
    {
        private readonly IHubContext<VotingHub> _votingHub;
        public VoteController(IHubContext<VotingHub> votingHub)
        {
            _votingHub = votingHub;
        }


        public IActionResult Index()
        {
            int Voted = 1; // Return from database if the user have been voted or not
                           // 0 means didn't vote
                           // 1 voted for option A
                           // 2 voted for option B

            int countA = 300; // From database count of votes for option A from user table
            int countB = 300; // From database count of votes for option A from user table

            ViewBag.CountA = countA;
            ViewBag.CountB = countB;

            return View(Voted);
        }

        public IActionResult Vote1()
        {
            // Ensuring that the user has not already voted.
            // Update the vote in user table database.

            _votingHub.Clients.All.SendAsync("UpdateVoteCount", "A");
            return RedirectToAction("Index");
        }

        public IActionResult Vote2()
        {
            // Ensuring that the user has not already voted.
            // Update the vote in user table database.

            _votingHub.Clients.All.SendAsync("UpdateVoteCount", "B");
            return RedirectToAction("Index");
        }
    }
}
