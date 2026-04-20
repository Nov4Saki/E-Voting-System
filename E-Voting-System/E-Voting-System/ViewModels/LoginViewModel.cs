using System.ComponentModel.DataAnnotations;

namespace E_Voting_System.ViewModels
{
    public class LoginViewModel
    {
        [Required(ErrorMessage = $"You must upload the Id Image file.")]
        public IFormFile IdImage { get; set; } = null!;

        [Required(ErrorMessage = $"You must upload Selfie with the Id Image file.")]
        public IFormFile SelfieImage { get; set; } = null!;
    }
}
