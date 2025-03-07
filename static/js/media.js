import { navbar } from './base.js';

export async function load_github_data(github_url){
    const followingPlaceholder = document.getElementById('following_placeholder');
    const followingContent = document.getElementById('n_following');

    const followersPlaceholder = document.getElementById('followers_placeholder');
    const followersContent = document.getElementById('n_followers');

    const githubImgPlaceholder = document.getElementById('github_img_placeholder');
    const githubImgContent = document.getElementById('github_img');
    
    const githubNamePlaceholder = document.getElementById('github_name_placeholder');
    const githubNameContent = document.getElementById('github_name');

    const response = await fetch(github_url);
    const github_data = await response.json();

    followingPlaceholder.classList.add('hidden'); // Hide the placeholder
    followingContent.classList.remove('hidden'); // Show the actual data
    followingContent.innerHTML = github_data.following

    followersPlaceholder.classList.add('hidden'); // Hide the placeholder
    followersContent.classList.remove('hidden'); // Show the actual data
    followersContent.innerHTML = github_data.followers

    githubImgPlaceholder.classList.add('hidden'); // Hide the placeholder
    githubImgContent.classList.remove('hidden'); // Show the actual data
    githubImgContent.src = github_data.avatar_url;

    githubNamePlaceholder.classList.add('hidden'); // Hide the placeholder
    githubNameContent.classList.remove('hidden'); // Show the actual data
    githubNameContent.innerHTML = github_data.login
}


export async function load_leetcode_data(leetcode_url) {

    const response = await fetch(leetcode_url);
    const leetcode_data = await response.json();
    
    // // Update username
    document.getElementById('leetcode_name').textContent = leetcode_data.user.username;
    document.getElementById('leetcode_name').classList.remove('hidden');
    document.getElementById('leetcode_name_placeholder').classList.add('hidden');

    // // Update profile image
    document.getElementById('leetcode_img').src = leetcode_data.user.avatar	;
    document.getElementById('leetcode_img').classList.remove('hidden');
    document.getElementById('leetcode_img_placeholder').classList.add('hidden');

    // Update problem counts and progress bars
    const updateStats = (easy, medium, hard) => {
        document.getElementById('easy_problems').textContent = easy;
        document.getElementById('easy_problems').classList.remove('hidden');
        document.getElementById('easy_placeholder').classList.add('hidden');
        document.getElementById('easy_progress').style.width = `${(easy / (easy + medium + hard)) * 100}%`;

        document.getElementById('medium_problems').textContent = medium;
        document.getElementById('medium_problems').classList.remove('hidden');
        document.getElementById('medium_placeholder').classList.add('hidden');
        document.getElementById('medium_progress').style.width = `${(medium / (easy + medium + hard)) * 100}%`;

        document.getElementById('hard_problems').textContent = hard;
        document.getElementById('hard_problems').classList.remove('hidden');
        document.getElementById('hard_placeholder').classList.add('hidden');
        document.getElementById('hard_progress').style.width = `${(hard / (easy + medium + hard)) * 100}%`;
    };

    updateStats(
        leetcode_data.profile.easySolved, 
        leetcode_data.profile.mediumSolved, 
        leetcode_data.profile.hardSolved
    )

}