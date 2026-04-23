using System.Diagnostics;
using E_Voting_System.Entities;
using E_Voting_System.Models;
using E_Voting_System.ViewModels;
using Microsoft.AspNetCore.Mvc;
using Microsoft.IdentityModel.Tokens;

namespace E_Voting_System.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly AppDbContext _context;

        public HomeController(ILogger<HomeController> logger, AppDbContext context)
        {
            _logger = logger;
            _context = context;
        }

        public IActionResult Index()
        {
            if (Request.Cookies["UserId"] != null)
                return RedirectToAction("Index", "Vote");

            return View();
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult Login(LoginViewModel vm)
        {
            if (!ModelState.IsValid)
                return RedirectToAction("Index");

            var tempId = Request.Cookies["UserId"];

            try
            {
                if(tempId.IsNullOrEmpty())
                {
                    tempId = Guid.NewGuid().ToString("N").Substring(0, 14);
                    Response.Cookies.Append("UserId", tempId, new CookieOptions
                    {
                        Expires = DateTimeOffset.UtcNow.AddMinutes(30),
                        HttpOnly = true,
                        IsEssential = true,
                        Secure = true,
                        SameSite = SameSiteMode.Strict
                    });
                }
                var user = _context.Users.Find(tempId);
                if(user == null)
                {
                    _context.Users.Add(new User { Id = tempId!, Vote = 0 });
                    _context.SaveChanges();
                }
            }
            catch(Exception ex)
            {
                Response.Cookies.Delete("UserId");
                Console.WriteLine(ex.Message);
                return View("Index");
            }

            return RedirectToAction("Index", "Vote");
        }

        public IActionResult Logout()
        {
            if (Request.Cookies["UserId"] != null)
                Response.Cookies.Delete("UserId");

            return RedirectToAction("Index");
        }


        
        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
