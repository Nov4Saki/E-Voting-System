using E_Voting_System.Entities;
using E_Voting_System.Hubs;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;

namespace E_Voting_System.Controllers
{
    public class VoteController : Controller
    {
        private readonly IHubContext<VotingHub> _votingHub;
        private readonly AppDbContext _context;
        public VoteController(IHubContext<VotingHub> votingHub, AppDbContext context)
        {
            _votingHub = votingHub;
            _context = context;
        }


        public  async Task<IActionResult> Index()
        {
            if (Request.Cookies["UserId"] == null)
                return RedirectToAction("Index", "Home");


            int voted = 0;
            
            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == Request.Cookies["UserId"]);

            if (user == null)
                return NotFound();

            voted = user.Vote;
                

            int countA = await _context.Users.CountAsync(u=>u.Vote == 1); 
            int countB = await _context.Users.CountAsync(u => u.Vote == 2);  

            ViewBag.CountA = countA;
            ViewBag.CountB = countB;
            
            return View(voted);

        }

        public async Task<IActionResult> Vote1()
        {
            if (Request.Cookies["UserId"] == null)
                return RedirectToAction("Index", "Home");

            int voted = 0;

            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == Request.Cookies["UserId"]);

            if (user == null)
                return NotFound();

            voted = user.Vote;

            if(voted == 0)
            {
                try
                {
                    user.Vote = 1;
                    _context.SaveChanges();
                    await _votingHub.Clients.All.SendAsync("UpdateVoteCount", "A");
                }catch(Exception ex)
                {
                    Console.WriteLine(ex.Message);
                    return View("Index");
                }

            }
            
            return RedirectToAction("Index");
        }

        public async Task<IActionResult> Vote2()
        {
            if (Request.Cookies["UserId"] == null)
                return RedirectToAction("Index", "Home");

            int voted = 0;

            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == Request.Cookies["UserId"]);

            if (user == null)
                return NotFound();

            voted = user.Vote;

            if (voted == 0)
            {
                try
                {
                    user.Vote = 2;
                    _context.SaveChanges();
                    await _votingHub.Clients.All.SendAsync("UpdateVoteCount", "B");
                }
                catch (Exception ex)
                {
                    Console.WriteLine(ex.Message);
                    return View("Index");
                }

            }
            
            return RedirectToAction("Index");
        }
    }
}
